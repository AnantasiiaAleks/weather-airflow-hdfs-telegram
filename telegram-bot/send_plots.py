# telegram-bot/send_plots.py

import argparse
from weather_utils import read_from_hdfs, generate_plot, send_photo

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--hdfs-path', default="/raw/weather/latest/raw_weather.json")
    parser.add_argument('--bot-token', required=True)
    parser.add_argument('--chat-id', required=True)
    args = parser.parse_args()

    try:
        # Читаем данные из HDFS
        df = read_from_hdfs(args.hdfs_path)

        # Строим график
        plot_path = generate_plot(df)

        # Отправляем в Telegram
        send_photo(args.bot_token, args.chat_id, plot_path)
        print("✅ График успешно отправлен!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        exit(1)


if __name__ == "__main__":
    main()