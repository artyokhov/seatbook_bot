# services/user_service.py
import datetime

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db_session
from db.models import Booking, User


class UserService:

    @staticmethod
    async def get_user_by_tg_id(tg_id: int) -> User | None:
        """Получить пользователя по Telegram ID."""
        async for session in get_db_session():
            try:
                result = await session.execute(select(User).where(User.tg_id == tg_id))
                return result.scalar_one_or_none()
            except Exception as e:
                await session.rollback()
                raise ValueError(f"Error getting user by tg_id: {e}")

    @staticmethod
    async def get_users_wo_tg_id(page: int = 0) -> dict | None:
        """Получить список пользователей, у которых tg_id is NULL с пагинацией по 10"""
        async for session in get_db_session():
            try:
                # Получаем общее количество пользователей без tg_id
                total_count_result = await session.execute(
                    select(func.count(User.id)).where(User.tg_id.is_(None))
                )
                total_count = total_count_result.scalar()

                # Получаем пользователей для текущей страницы
                page_size = 10
                result = await session.execute(
                    select(User)
                    .where(User.tg_id.is_(None))
                    .order_by(User.full_name)
                    .offset(page * page_size)
                    .limit(page_size)
                )
                users = result.scalars().all()

                return {
                    "users": list(users) if users else [],
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (
                        (total_count + page_size - 1) // page_size
                        if total_count > 0
                        else 0
                    ),
                }

            except Exception:
                await session.rollback()
                raise ValueError

    @staticmethod
    async def get_users_w_tg_id(page: int = 0) -> dict | None:
        """Получить список пользователей, у которых tg_id is not NULL с пагинацией по 10"""
        async for session in get_db_session():
            try:
                # Получаем общее количество пользователей c tg_id
                total_count_result = await session.execute(
                    select(func.count(User.id)).where(User.tg_id.is_not(None))
                )
                total_count = total_count_result.scalar()

                # Получаем пользователей для текущей страницы
                page_size = 10
                result = await session.execute(
                    select(User)
                    .where(User.tg_id.is_not(None))
                    .order_by(User.full_name)
                    .offset(page * page_size)
                    .limit(page_size)
                )
                users = result.scalars().all()

                return {
                    "users": list(users) if users else [],
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (
                        (total_count + page_size - 1) // page_size
                        if total_count > 0
                        else 0
                    ),
                }

            except Exception as e:
                await session.rollback()
                raise ValueError(f"Error getting users with tg_id: {e}")

    @staticmethod
    async def get_user_by_user_id(user_id: int) -> User | None:
        """Получить данные пользователя по id из таблицы users."""
        async for session in get_db_session():
            result = await session.execute(select(User).where(User.id == user_id))

            return result.scalar_one_or_none()

    @staticmethod
    async def update_user(
        user_id: int, username: str | None, tg_id: int | None, chat_id: int | None
    ) -> User:
        """Обновить существующего пользователя с указанным user_id."""
        async for session in get_db_session():
            try:
                # Находим пользователя по user_id
                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()

                if not user:
                    raise ValueError(f"Сбой регистрации, обратитесь в поддержку.")

                # Обновляем данные пользователя
                user.username = username
                user.tg_id = tg_id
                user.chat_id = chat_id

                await session.commit()
                await session.refresh(user)
                return user

            except Exception as e:
                await session.rollback()
                raise ValueError(f"Error updating user: {e}")

    @staticmethod
    async def untie_user_tg_id(user_id: int) -> None:
        """
        Отвязать tg_id от ФИО:
        1. Удалить все бронирования пользователя (любого типа).
        2. В таблице users для user_id обнулить все поля, кроме full_name и id.
        """
        async for session in get_db_session():
            try:
                # 1. Удаляем все бронирования пользователя
                await session.execute(delete(Booking).where(Booking.user_id == user_id))

                # 2. Обнуляем поля в users (оставляем только full_name и id)
                await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(username=None, tg_id=None, chat_id=None)
                )

                await session.commit()

            except Exception as e:
                await session.rollback()
                raise ValueError(f"Error untie user: {e}")

    @staticmethod
    async def get_all_fullnames(page: int = 0) -> dict:
        """
        Получить список всех ФИО из таблицы users.
        """
        async for session in get_db_session():
            try:
                # Получаем общее количество пользователей без tg_id
                total_count_result = await session.execute(select(func.count(User.id)))

                total_count = (
                    total_count_result.scalar()
                )  # Получаем пользователей для текущей страницы
                page_size = 10

                result = await session.execute(
                    select(User)
                    .order_by(User.full_name)
                    .offset(page * page_size)
                    .limit(page_size)
                )
                users = result.scalars().all()

                return {
                    "users": list(users) if users else [],
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (
                        (total_count + page_size - 1) // page_size
                        if total_count > 0
                        else 0
                    ),
                }

            except Exception as e:
                await session.rollback()
                raise ValueError(f"Error getting free users: {e}")

    @staticmethod
    async def delete_user(user_id: int) -> None:
        """
        Удалить сотрудника:
        1. Удалить все бронирования пользователя (любого типа).
        2. В таблице users удалить запись для user_id (ФИО станет недоступно для регистрации).
        """
        async for session in get_db_session():
            try:
                # 1. Удаляем все бронирования пользователя
                await session.execute(delete(Booking).where(Booking.user_id == user_id))

                # 2. Удаляем пользователя
                await session.execute(delete(User).where(User.id == user_id))

                await session.commit()

            except Exception as e:
                await session.rollback()
                raise ValueError(f"Error deleting user: {e}")

    @staticmethod
    async def add_user(full_name: str) -> User:
        """
        Создать пользователя в таблице users:
        - full_name = переданное ФИО
        - остальные поля = NULL
        """
        async for session in get_db_session():
            try:
                # Проверяем, что такого ФИО еще нет
                existing_user = await session.execute(
                    select(User.id).where(User.full_name == full_name)
                )
                if existing_user.scalar_one_or_none():
                    raise ValueError(
                        f"User with full_name '{full_name}' already exists"
                    )

                # Создаем пользователя
                new_user = User(full_name=full_name)

                session.add(new_user)

                await session.commit()
                return new_user

            except Exception as e:
                await session.rollback()
                raise ValueError(f"Error adding user '{full_name}': {e}")
