# 🛠 Установка и запуск

В этом разделе ты найдёшь пошаговую инструкцию по развёртке проекта локально или на сервере.

---

## 📋 Предварительные требования

- Docker (версия 20+)
- Docker Compose (версия 2+)
- Python 3.8+
- Git

---

## 📥 Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/your_username/weather-airflow-hdfs-telegram.git 
cd weather-airflow-hdfs-telegram
```

## 📄 Шаг 2: Настройка переменных окружения
Создай .env файл из шаблона:

```bash
cp .env.example .env
```

Отредактируй его:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
AIRFLOW_UID=50000
```

## ▶️ Шаг 3: Запуск через Docker Compose
```bash
docker-compose up -d
```
Подожди 1–2 минуты, пока все контейнеры запустятся.

## 🌐 Шаг 4: Открытие Airflow UI
🔗 Перейди по адресу:
http://localhost:8080

Логин: airflow
Пароль: airflow

## 🤖 Шаг 5: Запуск DAG’а вручную

1. Включи DAG weather_monthly_pipeline
2. Нажми кнопку "Trigger DAG"
3. Убедись, что данные записаны в HDFS
4. Проверь, пришёл ли график в Telegram

## 📣 Шаг 6: Запуск Telegram-бота
Бот уже запущен внутри контейнера. Просто напиши ему /start, /forecast, /choose или /weather Москва.

## 🧪 Что делать, если что-то не работает?
Смотри:

 - Логи контейнеров: docker logs <container_name>
 - [README.md](.././README.md) → там тоже есть инструкция
 - [troubleshooting.md](troubleshooting.md) → список частых проблем и решений