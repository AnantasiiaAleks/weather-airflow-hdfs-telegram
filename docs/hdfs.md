# 🗃️ HDFS в проекте

HDFS используется как хранилище сырых данных. Для работы с ним применяется **WebHDFS REST API** вместо официального клиента.

---

## 🔧 Как это работает

### 1. Создание файла

```bash
PUT http://namenode:50070/webhdfs/v1/raw/weather/latest/raw_weather.json?op=CREATE&user=airflow&overwrite=True
```
### 2. Чтение файла
```bash
GET http://namenode:50070/webhdfs/v1/raw/weather/latest/raw_weather.json?op=OPEN
```

### 3. Создание директории
```bash
PUT http://namenode:50070/webhdfs/v1/raw/weather/latest?op=MKDIRS
```

### 📁 Структура HDFS
```
/raw/
  └── weather/
      ├── 2025-06-01/
      │   └── raw_weather.json
      ├── 2025-05-01/
      │   └── raw_weather.json
      └── latest/
          └── raw_weather.json
```

### 🧰 Формат данных
JSON-файл содержит поля:

- time: дата и время
- tavg: средняя температура
- tmin, tmax: мин/макс температура
- wspd: скорость ветра
- prcp: осадки
- pres: давление
- city: название города