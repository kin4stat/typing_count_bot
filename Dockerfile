# Используйте официальный образ Python
FROM python:3.8

# Установите рабочий каталог в контейнере
WORKDIR /app

# Скопируйте файлы зависимостей и установите их
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируйте исходный код в контейнер
COPY ./main.py ./

# Запуск скрипта
CMD ["python", "./main.py"]