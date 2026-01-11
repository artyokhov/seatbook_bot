import os
from pathlib import Path

from dotenv import load_dotenv

# Определяем среду выполнения (по умолчанию 'dev')
APP_ENV = os.getenv("APP_ENV", "dev")
print("Среда запуска: ", APP_ENV)

# Выбираем файл .env в зависимости от среды
env_file = f".env.{APP_ENV}"
env_path = Path(".") / env_file
print("Файл переменных окружения: ", env_path)

if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    # Для Docker контейнера используем переменные окружения напрямую
    load_dotenv(override=True)


class Settings:
    # бот всегда берет токен из переменной BOT_TOKEN,
    # значение которой зависит от загруженного .env файла
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    # Настройки БД
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "seatbook_bot_dev")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASS = os.getenv("DB_PASS", "password")
    DATABASE_URL = (
        f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    # список юзернеймов которым доступна панель администратора
    ADMIN_USERNAMES_LIST = [
        u.strip().lower().lstrip("@")
        for u in os.getenv("ADMIN_USERNAMES", "").split(",")
        if u.strip()
    ]
    # основной админ, в чей чат предзаливаются png/jpeg для получения file_id
    ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", 0))
    OFFICE_MAP_PATH = os.getenv("OFFICE_MAP_PATH", "static/office_map.png")
    raw_users = os.getenv("USERS_LIST", "")
    USERS_LIST = [u.strip() for u in raw_users.splitlines() if u.strip()]
    # USERS_LIST = (
    #     list(map(str, os.getenv("USERS_LIST", "").split(",")))
    #     if os.getenv("USERS_LIST")
    #     else []
    # )
    EXISTING_SEATS_LIST = (
        list(map(str, os.getenv("EXISTING_SEATS_LIST", "").split(",")))
        if os.getenv("EXISTING_SEATS_LIST")
        else []
    )

    PLANNING_DAYS = int(os.getenv("PLANNING_DAYS", 14))


print("DB_HOST from env:", os.getenv("DB_HOST"))
print("DB_PORT from env:", os.getenv("DB_PORT"))
print("DB_NAME from env:", os.getenv("DB_NAME"))
print("DB_USER from env:", os.getenv("DB_USER"))


settings = Settings()
