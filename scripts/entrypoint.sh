#!/bin/bash
set -e

# отладка
echo "DB_HOST=${DB_HOST}"
echo "DB_PORT=${DB_PORT}"
echo "DB_USER=${DB_USER}"
echo "DB_NAME=${DB_NAME}"

# Ждем готовности БД
sleep 2
echo "Waiting for database ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "${DB_HOST}" -p "${DB_PORT}"; do
    sleep 1
done
echo "Database is ready!"

# Создаем таблицы через SQLAlchemy
echo "Creating database tables using SQLAlchemy..."
python /app/scripts/init_tables.py

# Даем время на завершение создания таблиц
sleep 2

# Проверяем существование таблицы users перед инициализацией
echo "Checking if users table exists..."
if pg_isready -h "${DB_HOST}" -p "${DB_PORT}"; then
    if PGPASSWORD="${DB_PASS}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "\dt seatbook.users" | grep -q "users"; then
        echo "Users table exists, proceeding with user initialization..."
        
        # Инициализируем пользователей
        if [ "$INIT_USERS" = "true" ]; then
            echo "Initializing users from USERS_LIST..."
            python /app/scripts/init_users.py
        fi
    else
        echo "ERROR: Users table does not exist! Skipping user initialization."
    fi
else
    echo "ERROR: Database not ready for user initialization!"
fi

# Запускаем приложение
exec "$@"