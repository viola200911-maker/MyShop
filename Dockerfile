# Використовуємо офіційний легкий образ Python
FROM python:3.10-slim

# Забороняємо Python писати .pyc файли та буферизувати stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Встановлюємо системні бібліотеки, необхідні для компіляції (PostgreSQL, Pillow тощо)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Встановлюємо робочу директорію всередині контейнера
WORKDIR /app

# Копіюємо та встановлюємо залежності
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копіюємо весь код проєкту
COPY . /app/

# Запускаємо сервер через gunicorn (замініть 'myproject' на назву папки, де лежить ваш wsgi.py)
CMD python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    gunicorn myproject.wsgi:application --bind 0.0.0.0:10000 --timeout 30