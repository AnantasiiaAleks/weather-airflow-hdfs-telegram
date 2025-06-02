# 🌤️ Weather Monthly Pipeline

Проект собирает исторические данные о погоде для трёх городов (Москва, Санкт-Петербург, Сочи), сохраняет их в HDFS, строит график температуры и отправляет его через Telegram.

👉 Подробнее в [Документации](index.md)

---

## 📁 Что в репозитории

| Файл | Описание |
| --- | --- |
| docker-compose.yml | Оркестровка контейнеров |
| requirements.txt | Список зависимостей |
| README.md | Описание проекта, инструкция по запуску |
| dags/weather_monthly_dag.py | DAG Airflow |
| telegram-bot/bot.py | Основной Telegram-бот |
| telegram-bot/send_plots.py | Для вызова из Airflow |
| telegram-bot/weather_utils.py | Общие функции: HDFS, график, чтение/запись |
| docs/ | Документация проекта |

---

## 🧩 Функционал

- Получение данных о погоде за последний месяц из [Meteostat](https://dev.meteostat.net/) 
- Сохранение в HDFS через WebHDFS REST API
- Построение графика температуры по дням (`matplotlib`, `seaborn`)
- Отправка графика через Telegram-бота

---

## 📁 Структура проекта
```
weather-plots/
├── .env # Переменные окружения
├── docker-compose.yml # Оркестровка контейнеров
├── requirements.txt # Python-зависимости
├── dags/ # DAG'и Airflow
│ └── weather_monthly_dag.py
├── telegram-bot/
│ ├── bot.py # Запускаемый бот
│ ├── send_plots.py # CLI-скрипт для Airflow
│ └── weather_utils.py # Вспомогательные функции
├── hdfs-data/ # Данные NameNode и DataNode
│ ├── namenode/
│ └── datanode/
├── logs/ # Логи Airflow
├── data/ # Временные файлы
└── docs/ # Документация проекта
```


---

## ⚙️ Требования

- Docker + Docker Compose установлен
- Telegram Bot Token (получается у [@BotFather](https://t.me/BotFather)) 
- Chat ID (можно получить, написав `/start` своему боту)

---

## 🛠 Установка

### 1. Клонируй репозиторий

```bash
git clone https://github.com/yourusername/weather-plots.git 
cd weather-plots
```

### 2. Создай .env файл

Пример .env:
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
AIRFLOW_UID=50000
```

---

### 🔧 Установка зависимостей

Все зависимости ставятся автоматически при запуске через docker-compose.

💡 Никаких провайдеров Airflow не требуется
✅ Используется только requests + WebHDFS REST API 

---

## ▶️ Запуск проекта

### 1. Поднимаем все контейнеры

```bash
docker-compose up -d
```

### 2. Активируем DAG в UI

Перейди в Airflow Webserver → активируй DAG weather_monthly_pipeline

---

## 📊 Работа с данными

DAG запускается ежемесячно или вручную:

Получает данные из Meteostat
Сохраняет в HDFS: /raw/weather/{{ ds }}/raw_weather.json
Читает данные из HDFS
Строит график температуры по дням
Отправляет график через Telegram

---

## 📦 Технические детали

- Используется WebHDFS REST API вместо hdfscli и провайдеров Airflow
- Все данные хранятся в HDFS
- Бот использует python-telegram-bot==13.15
- Airflow 2.9.3 + CeleryExecutor + Redis + PostgreSQL

---

## 📣 Команды бота


 /start | Приветствие бота 
 --- | --- 
 /forecast | Вывод графика 
 /weather <город> | информация о погоде в городе 
 /choose | выбор города кнопками 

---

## 🚀 Что дальше?

- расширить список городов
- сделать возможность вывода графика по городам по выбору и за выбранный период
- изменить вывод информации о погоде (на текущий момент показывает среднюю температуру за прошедший месяц => сделать вывод текущей ситуации)
- "спрятать" вводимые команды, сделать кнопками