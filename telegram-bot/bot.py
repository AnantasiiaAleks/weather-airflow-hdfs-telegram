# telegram-bot/bot.py

from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
import os
from weather_utils import get_weather_for_city, generate_plot, read_from_hdfs


SUPPORTED_CITIES = ['Moscow', 'Saint Petersburg', 'Adler']


# === Команда /start ===
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Привет, {user.mention_markdown_v2()}\! Я бот прогноза погоды\.',
        reply_markup=ForceReply(selective=True),
    )


# === Команда /help ===
def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Доступные команды:\n"
        "/start — Приветствие\n"
        "/help — Список команд\n"
        "/forecast — Получить график температуры\n"
        "/weather <город> — Текстовый прогноз погоды для города\n"
        "/choose — Выбрать город через кнопки\n"
        "Поддерживаемые города: Moscow, Saint Petersburg, Adler"
    )


# === Команда /forecast ===
def forecast(update: Update, context: CallbackContext) -> None:
    try:
        update.message.reply_text("⏳ Создаю график...")
        df = read_from_hdfs("/raw/weather/latest/raw_weather.json")
        plot_path = generate_plot(df)
        with open(plot_path, 'rb') as photo:
            update.message.reply_photo(photo=photo, caption="📈 График температуры за последний месяц")
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка при получении данных: {str(e)}")


# === Команда /weather Москва ===

def send_city_weather(context, city, chat_id):
    """Отправляет текстовое описание погоды для конкретного города"""
    try:
        df = read_from_hdfs("/raw/weather/latest/raw_weather.json")
        city_df = df[df['city'] == city].iloc[-1:]

        if city_df.empty:
            context.bot.send_message(chat_id=chat_id, text="❌ Нет данных для этого города")
            return

        latest = city_df.iloc[0]
        message = (
            f"🌤️ Последние данные о погоде в *{latest['city']}*:\n"
            f"🌡 Средняя температура: {latest['tavg']}°C\n"
            f"🧣 Мин/макс температура: {latest['tmin']}–{latest['tmax']}°C\n"
            f"💧 Осадки: {latest['prcp']} мм\n"
            f"🌬 Скорость ветра: {latest['wspd']} м/с\n"
            f"🔽 Давление: {latest['pres']} гПа"
        )
        context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
    except Exception as e:
        context.bot.send_message(chat_id=chat_id, text=f"❌ Ошибка: {str(e)}")


def weather(update: Update, context: CallbackContext) -> None:
    if not context.args:
        update.message.reply_text('❗ Укажите город. Пример: /weather Moscow')
        return

    requested_city = " ".join(context.args).strip().title()

    if requested_city not in SUPPORTED_CITIES:
        update.message.reply_text(
            f"❌ К сожалению, я не поддерживаю этот город.\n"
            f"Доступные города: {', '.join(SUPPORTED_CITIES)}"
        )
        return

    send_city_weather(context, requested_city, update.message.chat.id)


# === Команда /choose — выбор города через кнопки ===
def choose_city(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton(city, callback_data=f"city_{city}") for city in SUPPORTED_CITIES]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите город:', reply_markup=reply_markup)


# === Обработчик нажатия кнопок ===
def button_weather_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    city = query.data.replace("city_", "")
    send_city_weather(context, city, query.message.chat.id)


# === Запуск бота ===
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("forecast", forecast))
    dispatcher.add_handler(CommandHandler("weather", weather))
    dispatcher.add_handler(CommandHandler("choose", choose_city))
    dispatcher.add_handler(CallbackQueryHandler(button_weather_handler))

    print("🤖 Бот запущен. Ctrl+C для остановки.")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    main()