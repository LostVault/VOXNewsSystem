FROM python:3.10.0-slim-buster

# Задаём рабочий каталог
RUN mkdir -p /workdir
WORKDIR /workdir

# Копируем файлы в рабочий каталог
COPY requirements.txt requirements.txt

# Обновляем pip
RUN pip install --upgrade pip

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем файлы в рабочий каталог
COPY . .

# Выполняем команду
CMD [ "python3", "main.py"]