import asyncio
import os
import sys

sys.stdout.reconfigure(line_buffering=True)

# Добавляем корневую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from db.database import Base, engine
from db.models import Booking, User


async def init_database():
    """Инициализация базы данных - создание таблиц"""
    print("Starting database initialization...")

    try:
        # Создаем все таблицы
        async with engine.begin() as conn:
            print("Creating tables...")
            whoami = await conn.execute(text("SELECT current_user, session_user"))
            print("Connected as:", list(whoami))
            await conn.execute(text("SHOW search_path"))
            sp = await conn.execute(text("SHOW search_path"))
            print("Search path:", list(sp))
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS seatbook"))
            await conn.run_sync(Base.metadata.create_all)
            print("Tables created successfully!")

        print("Database initialized successfully!")
        return True

    except Exception as e:
        print(f"Error during database initialization: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(init_database())
