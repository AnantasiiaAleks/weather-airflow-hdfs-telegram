# 🔧 Troubleshooting: часто возникающие проблемы

В этом разделе собраны **наиболее распространённые ошибки** и способы их устранения для проекта `weather-airflow-hdfs-telegram`.

---

## ❌ Ошибка: `could not translate host name "postgres" to address`

### 💡 Причина:
Airflow не может подключиться к PostgreSQL по имени хоста.

### ✅ Решение:
1. Убедись, что сервис `postgres` запущен:

   ```bash
   docker ps -a | grep postgres
   ```
2. Проверь, задан ли hostname: postgres в docker-compose.yml:
```yaml
postgres:
  hostname: postgres
  container_name: weather-plots-postgres-1
```
3. Убедись, что все контейнеры находятся в одной сети Docker:
```yaml
networks:
  - airflow-network
```
4. Перезапусти контейнеры:
```bash
docker-compose down
docker-compose up -d
```

## ❌ Ошибка: FileAlreadyExistsException

### 💡 Причина:
Попытка записи файла в HDFS, если он уже существует.

### ✅ Решение:
Добавь параметр overwrite=True в URL создания файла:
```python
create_url = f"{HDFS_NAMENODE}{hdfs_path}?op=CREATE&user={HDFS_USER}&overwrite=True"
```
Или добавь автоматическое удаление старого файла перед записью:
```python
requests.delete(f"{HDFS_NAMENODE}{hdfs_path}?op=DELETE&recursive=True&user.name={HDFS_USER}")
```

## ❌ Ошибка: Chat not found

### 💡 Причина:
Неверно указан TELEGRAM_CHAT_ID или бот не имеет доступа к этому чату.

### ✅ Решение:
Получи точный chat_id, написав /start своему Telegram-боту.
Обнови .env файл:
```bash
TELEGRAM_CHAT_ID=ваш_chat_id_здесь
```
Перезапусти контейнер бота:
```bash
docker-compose restart weather-telegram-bot
```

## ❌ Ошибка: Name or service not known

### 💡 Причина:
Контейнер не может найти другой сервис по имени (namenode, redis, postgres)

### ✅ Решение:
Убедись, что имя сервиса указано верно в docker-compose.yml

Все контейнеры должны использовать одинаковую сеть:
```yaml
networks:
  - airflow-network
```
Внутри контейнера проверь DNS:
```bash
docker exec -it weather-telegram-bot ping namenode
```
Если пинг не работает — пересобери контейнеры:
```bash
docker-compose down
docker-compose up -d
```

## ❌ Ошибка: Expected file path name or file-like object, got <class 'bytes'> type
### 💡 Причина:
Вы используете pandas.read_json(response.content) напрямую, но response.content — это bytes, а не file-like объект.

### ✅ Решение:
Используйте io.BytesIO:
```python
import pandas as pd
from io import BytesIO

df = pd.read_json(BytesIO(response.content))
```
или через JSON-строку:
```python
import json
df = pd.read_json(json.loads(response.text))
```

## ❌ Ошибка: Connection refused при работе с HDFS

### 💡 Причина:
HDFS NameNode или DataNode не запущен / недоступен.

### ✅ Решение:
Проверь статус контейнеров:
```bash
docker ps -a
```
Посмотри логи:
```bash
docker logs namenode
docker logs datanode
```
Убедись, что порты проброшены правильно:
```yaml
ports:
  - "50070:50070"  # WebHDFS
  - "9000:9000"    # RPC
```
Проверь, доступен ли HDFS из контейнера Airflow:
```bash
docker exec -it weather-plots-airflow-webserver-1 curl "http://namenode:50070/webhdfs/v1/?op=GETHOMEDIRECTORY"
```

## ❌ Ошибка: ModuleNotFoundError: No module named 'meteostat'

### 💡 Причина:
Зависимости не установлены внутри контейнера Airflow

### ✅ Решение:
Убедись, что requirements.txt монтируется в контейнер:
```yaml
volumes:
  - ./requirements.txt:/requirements.txt
```
Установи зависимости:
```bash
pip install meteostat requests pandas matplotlib seaborn python-telegram-bot==13.15
```
Или обнови command: в docker-compose.yml:
```yaml
command:
  - bash
  - -c
  - |
    pip install --no-cache-dir -r /requirements.txt && \
    airflow db init && \
    airflow webserver
```

## ❌ Ошибка: DAG не запускается или не активирован

### ✅ Решение:
Перейди в Airflow UI: http://localhost:8080
Найди weather_monthly_pipeline
Активируй его (ползунок вправо)
Выполни Manual Run

## ❌ Ошибка: Bot was blocked by the user или Forbidden

### 💡 Причина:
Бот был заблокирован пользователем или ещё не получил от него сообщений

### ✅ Решение:
Напишите боту вручную: /start
Убедитесь, что вы не заблокировали бота
Проверьте токен и Chat ID через curl:
```bash
curl https://api.telegram.org/bot<TOKEN>/getUpdates 
```

## ❌ Ошибка: No such file or directory при чтении HDFS

### ✅ Решение:
Проверь, действительно ли файл существует в HDFS:
```bash
curl -i "http://namenode:50070/webhdfs/v1/raw/weather/latest?op=LISTSTATUS"
```
Если нет → запустите DAG вручную в Airflow
Убедись, что latest создаётся корректно

## ❌ Ошибка: Not a directory при записи в HDFS

### ✅ Решение:
Создай родительские директории до записи:
```python
parent_dir = os.path.dirname(hdfs_path)
mkdirs_url = f"{HDFS_NAMENODE}{parent_dir}?op=MKDIRS&user.name={HDFS_USER}"
response = requests.put(mkdirs_url)
```
Или вручную:
```bash
curl -X PUT "http://namenode:50070/webhdfs/v1/raw/weather/latest?op=MKDIRS&user.name=airflow"
```

## ❌ Ошибка: Permission denied при записи в HDFS

### ✅ Решение:
Убедись, что ты указываешь правильного пользователя:
```
?op=CREATE&user=airflow
```
Проверь права в hdfs-site.xml или core-site.xml

Или используй chmod через WebHDFS:
```bash
curl -X PUT "http://namenode:50070/webhdfs/v1/raw/weather?op=SETOWNER&user.name=airflow&owner=airflow
```

## 🛠 Полезные команды диагностики

ЧТО ПРОВЕРИТТЬ | КАК
--- | ---
Сетевые хосты | nslookup namenode, ping redis внутри контейнера
Логи Airflow | docker logs weather-plots-airflow-webserver-1
Логи HDFS | docker logs namenode, docker logs datanode
Тестовое подключение к HDFS | curl "http://namenode:50070/webhdfs/v1/?op=GETHOMEDIRECTORY"
Зависимости в боте | pip install python-telegram-bot==13.15