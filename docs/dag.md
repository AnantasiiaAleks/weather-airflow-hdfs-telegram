# 📈 DAG: weather_monthly_pipeline

Этот DAG собирает данные о погоде за последний месяц, сохраняет их в HDFS и отправляет график через Telegram.

---

## 🔄 Функционал

| Этап | Описание |
|------|----------|
| 1. fetch_and_save_to_hdfs | Получает данные от Meteostat и сохраняет в HDFS |
| 2. generate_plot | Читает данные из HDFS и строит график |
| 3. send_plot_telegram | Отправляет график через Telegram-бота |

---

## 📊 Конфигурации

- Запуск: `@monthly`
- Города: `Moscow`, `Saint Petersburg`, `Adler`
- HDFS путь: `/raw/weather/{{ ds }}/raw_weather.json`
- Telegram: использует `python-telegram-bot==13.15`

---

## 📝 Функции

### Получение данных

```python
def fetch_weather_data(**kwargs):
    ...
```

### Запись в HDFS
```python
def save_to_hdfs(df_json, hdfs_path):
    ...
```
### Чтение из HDFS
```python
def read_from_hdfs(hdfs_path):
    ...
```
### Построение графика
```python
def generate_plot(df, plot_path="/tmp/temperature_plot.png"):
    ...
```
### Отправка через Telegram
```python
def send_photo(bot_token, chat_id, plot_path):
    ...
```

### ⏱️ Расписание
```python
schedule_interval="@monthly"
```

DAG выполняется ежемесячно и сохраняет данные за прошедший месяц.