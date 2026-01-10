# Используем официальный Python образ
FROM python:3.13-slim-bookworm

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости + cron
RUN apt-get update && \
    apt-get install -y \
        gettext-base \
        postgresql-client \
        cron \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Добавляем cron-задачу
COPY docker/cron/clean_up_bookings /etc/cron.d/clean_up_bookings
RUN chmod 0644 /etc/cron.d/clean_up_bookings && \
    crontab /etc/cron.d/clean_up_bookings

# Копируем и делаем исполняемым entrypoint-скрипт
COPY ./scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Используем этот скрипт как точку входа
ENTRYPOINT ["/entrypoint.sh"]

# Запускаем cron + бота
CMD cron && python -m bot.main
