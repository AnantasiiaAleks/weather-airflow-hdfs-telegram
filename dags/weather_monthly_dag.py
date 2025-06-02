# dags/weather_monthly_dag.py

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
from datetime import datetime, timedelta
from datetime import timezone
import logging
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from meteostat import Daily
from telegram import Bot
import os
from io import BytesIO

# === Конфигурации и константы ===
TELEGRAM_BOT_TOKEN = Variable.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = Variable.get("TELEGRAM_CHAT_ID")

CITIES = {
    'Moscow': '27611',
    'Saint Petersburg': '27612',
    'Adler': '37171'
}

HDFS_NAMENODE = "http://namenode:50070/webhdfs/v1"
HDFS_USER = "airflow"

LOCAL_TEMP_DIR = "/tmp/hdfs_data/"
os.makedirs(LOCAL_TEMP_DIR, exist_ok=True)

RAW_HDFS_PATH = "/raw/weather/{{ ds }}/raw_weather.json"
HDFS_LATEST_PATH = "/raw/weather/latest/raw_weather.json"
PROCESSED_HDFS_PATH = "/processed/weather/{{ ds }}/temperature.png"


# === Функция получения данных и записи в HDFS ===

def fetch_weather_data(**kwargs):
    """Получает данные о погоде за последний месяц и возвращает DataFrame"""
    today = datetime.today()
    first_day = datetime(today.year, today.month - 1, 1)

    all_data = []

    for city, station_id in CITIES.items():
        data = Daily(station_id, start=first_day, end=today).fetch().reset_index()
        if data.empty:
            logging.warning(f"Нет данных для {city}")
            continue

        data['city'] = city
        all_data.append(data)

    if not all_data:
        raise Exception("❌ Не удалось получить данные ни для одного города")

    df = pd.concat(all_data, ignore_index=True)
    df['time'] = df['time'].astype(str)  # Чтобы избежать проблем при сериализации
    return df.to_json()


def save_to_hdfs(df_json, hdfs_path=None):
    """Сохраняет JSON в HDFS через WebHDFS REST API"""
    hdfs_path = hdfs_path or HDFS_RAW_PATH

    parent_dir = os.path.dirname(hdfs_path)

    mkdirs_url = f"{HDFS_NAMENODE}{parent_dir}?op=MKDIRS&user.name={HDFS_USER}"
    response = requests.put(mkdirs_url)

    if response.status_code not in (200, 201):
        logging.warning(f"⚠️ Не удалось создать директорию {parent_dir}: {response.text}")

    create_url = f"{HDFS_NAMENODE}{hdfs_path}?op=CREATE&user={HDFS_USER}&overwrite=True"

    response = requests.put(create_url, allow_redirects=False)
    if response.status_code != 307:
        raise Exception(f"❌ Ошибка создания файла в HDFS: {response.text}")

    datanode_url = response.headers['Location']
    response = requests.put(datanode_url, data=df_json, headers={'Content-Type': 'application/json'})
    if response.status_code != 201:
        raise Exception(f"❌ Ошибка записи в HDFS: {response.text}")

    logging.info(f"✅ Данные успешно записаны в HDFS: {hdfs_path}")


def read_from_hdfs(hdfs_path=None):
    """Читает данные из HDFS через WebHDFS REST API"""

    open_url = f"{HDFS_NAMENODE}{hdfs_path}?op=OPEN&user={HDFS_USER}"

    response = requests.get(open_url, allow_redirects=False)
    if response.status_code != 307:
        raise Exception(f"❌ Ошибка открытия файла в HDFS: {response.text}")

    datanode_url = response.headers['Location']
    response = requests.get(datanode_url)

    if response.status_code != 200:
        raise Exception(f"❌ Ошибка чтения данных из HDFS: {response.text}")

    # Исправленный вызов pandas
    try:
        df = pd.read_json(BytesIO(response.content))
        return df
    except ValueError as e:
        logging.error(f"❌ Не удалось прочитать JSON: {e}")
        raise
    


def generate_plot(df, output_path="/tmp/temperature_plot.png"):
    """Строит график температуры по дням для каждого города"""
    plt.figure(figsize=(14, 7))
    sns.lineplot(data=df, x="time", y="tavg", hue="city", marker="o")
    plt.xticks(rotation=45)
    plt.title("Средняя температура (°C) за последний месяц")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    return output_path


# === Задачи DAG'а ===
def fetch_and_save_to_hdfs(**kwargs):
    """Запрашивает данные и сохраняет в HDFS"""
    df_json = fetch_weather_data(**kwargs)
    
    # Сохраняем в HDFS
    
    hdfs_path = RAW_HDFS_PATH.replace("{{ ds }}", kwargs['ds'])
    latest_path = "/raw/weather/latest/raw_weather.json"

    # Сохраняем по дате
    save_to_hdfs(df_json, hdfs_path)

    # Дублируем в /latest/ для бота
    save_to_hdfs(df_json, "/raw/weather/latest/raw_weather.json")
    
    # Сохраняем путь в XCom
    ti = kwargs['ti']
    ti.xcom_push(key='hdfs_path', value=hdfs_path)


def build_and_send_plot(**kwargs):
    """Читает данные из HDFS, строит график и отправляет в Telegram"""
    ti = kwargs['ti']
    hdfs_path = ti.xcom_pull(task_ids='fetch_and_save_to_hdfs', key='hdfs_path')
    
    # Чтение из HDFS
    df = read_from_hdfs(hdfs_path)

    # Построение графика
    plot_path = "/tmp/temperature_plot.png"
    plot_path = generate_plot(df, plot_path)

    # Отправка через Telegram
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    with open(plot_path, 'rb') as photo:
        bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=photo, caption="📊 Температура за прошлый месяц")


# === DAG ===
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='weather_monthly_pipeline',
    default_args=default_args,
    description='A pipeline to fetch, store and visualize weather data via WebHDFS REST API',
    schedule_interval="@monthly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    fetch_task = PythonOperator(
        task_id='fetch_and_save_to_hdfs',
        python_callable=fetch_and_save_to_hdfs,
        provide_context=True,
    )

    plot_task = PythonOperator(
        task_id='generate_plot',
        python_callable=build_and_send_plot,
        provide_context=True,
    )

    # Связь задач
    fetch_task >> plot_task