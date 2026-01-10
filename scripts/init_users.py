import asyncio
import os
import sys

# Добавляем корневую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from config.settings import settings
from db.database import AsyncSessionLocal, engine
from db.models import User


async def init_users():
    """Инициализирует пользователей в БД из settings.USERS_LIST"""
    print("Checking and initializing users from USERS_LIST...")

    async with AsyncSessionLocal() as session:
        try:
            # Получаем всех существующих пользователей
            result = await session.execute(select(User.full_name))
            existing_users = {row[0] for row in result.all()}

            users_to_add = []
            for full_name in settings.USERS_LIST:
                if full_name not in existing_users:
                    new_user = User(
                        full_name=full_name, username=None, tg_id=None, chat_id=None
                    )
                    users_to_add.append(new_user)
                    print(f"Adding user: {full_name}")
                else:
                    print(f"User already exists: {full_name}")

            if users_to_add:
                # Добавляем всех пользователей и обрабатываем возможные конфликты
                for user in users_to_add:
                    try:
                        session.add(user)
                        await session.flush()  # Частичный коммит для проверки
                    except IntegrityError as e:
                        await session.rollback()
                        print(f"Duplicate user skipped: {user.full_name}")
                        # Продолжаем добавлять остальных пользователей
                        continue

                await session.commit()
                print(f"Successfully added {len(users_to_add)} new users")
            else:
                print("All users from USERS_LIST already exist in database")

        except Exception as e:
            print(f"Error initializing users: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(init_users())
