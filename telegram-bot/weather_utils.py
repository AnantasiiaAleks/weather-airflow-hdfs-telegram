# telegram-bot/weather_utils.py

import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
from io import BytesIO


# === Настройки ===
HDFS_NAMENODE = "http://namenode:50070/webhdfs/v1"
HDFS_USER = "airflow"

LOCAL_TEMP_DIR = "/tmp/telegram-bot/"
os.makedirs(LOCAL_TEMP_DIR, exist_ok=True)


# === Функции работы с HDFS (через WebHDFS REST API) ===
def save_to_hdfs(df, hdfs_path="/raw/telegram-bot/latest/weather.json"):
    """Сохраняет DataFrame в HDFS через WebHDFS"""
    df_json = df.to_json()

    create_url = f"{HDFS_NAMENODE}{hdfs_path}?op=CREATE&user={HDFS_USER}"
    response = requests.put(create_url, allow_redirects=False)

    if response.status_code != 307:
        raise Exception(f"❌ Ошибка создания файла в HDFS: {response.text}")

    datanode_url = response.headers['Location']
    response = requests.put(datanode_url, data=df_json, headers={'Content-Type': 'application/json'})

    if response.status_code != 201:
        raise Exception(f"❌ Ошибка записи данных в HDFS: {response.text}")

    print(f"✅ Данные записаны в HDFS: {hdfs_path}")
    return hdfs_path


# === Чтение из HDFS ===
def read_from_hdfs(hdfs_path):
    """Читает данные из HDFS через WebHDFS"""
    open_url = f"{HDFS_NAMENODE}{hdfs_path}?op=OPEN&user={HDFS_USER}"

    response = requests.get(open_url, allow_redirects=False)
    if response.status_code != 307:
        raise Exception(f"❌ Ошибка открытия файла в HDFS: {response.text}")

    datanode_url = response.headers['Location']
    response = requests.get(datanode_url)

    if response.status_code != 200:
        raise Exception(f"❌ Ошибка чтения из HDFS: {response.text}")

    df = pd.read_json(BytesIO(response.content))
    return df


# === Построение графика ===
def generate_plot(df, plot_path=None):
    """Строит линейный график температуры"""
    df['date'] = pd.to_datetime(df['time']).dt.date

    plt.figure(figsize=(14, 7))
    sns.lineplot(data=df, x="date", y="tavg", hue="city", marker="o")
    plt.xticks(rotation=45)
    plt.title("Средняя температура (°C) за последний месяц")
    plt.tight_layout()
    plot_path = plot_path or os.path.join(LOCAL_TEMP_DIR, "temperature_plot.png")
    plt.savefig(plot_path)
    plt.close()

    return plot_path


# === Отправка графика через Telegram Bot API ===
def send_photo(bot_token, chat_id, photo_path):
    """Отправляет фото в Telegram"""
    from telegram import Bot

    bot = Bot(token=bot_token)
    with open(photo_path, 'rb') as photo:
        bot.send_photo(chat_id=chat_id, photo=photo, caption="📊 Температура за прошлый месяц")


# === Получение погоды по городу ===
def get_weather_for_city(city, hdfs_path="/raw/weather/latest/raw_weather.json"):
    """Возвращает текстовое описание погоды по одному городу"""
    df = read_from_hdfs(hdfs_path)
    city_df = df[df['city'] == city]

    if city_df.empty:
        return f"❌ Нет данных о погоде для города {city}."

    latest = city_df.iloc[-1]
    message = (
        f"🌤️ Последние данные о погоде в *{latest['city']}*:\n"
        f"🌡 Средняя температура: {latest['tavg']}°C\n"
        f"🧣 Мин/макс температура: {latest['tmin']}–{latest['tmax']}°C\n"
        f"💧 Осадки: {latest['prcp']} мм\n"
        f"🌬 Скорость ветра: {latest['wspd']} м/с\n"
        f"🔽 Давление: {latest['pres']} гПа"
    )

    return message