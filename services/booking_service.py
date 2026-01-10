import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

import utils
from config.settings import settings
from db.database import get_db_session
from db.models import Booking, User
from services.errors import *


class BookingService:

    @staticmethod
    async def get_available_dates(tg_id: int) -> list[dict]:
        """
        Получить даты доступные для персонального бронирования места с учетом уже
        созданных бронирований пользователя и заполненности офиса.
        """
        upcoming_dates = await utils.generate_upcoming_dates()
        max_bookings_per_day = len(settings.EXISTING_SEATS_LIST)

        user_booked_dates = []
        bookings_count_by_date = {}

        async for session in get_db_session():
            try:
                # 1. Получаем даты, на которые у пользователя уже есть бронирования
                user_bookings_result = await session.execute(
                    select(Booking.booking_date)
                    .join(User, User.id == Booking.user_id)
                    .where(User.tg_id == tg_id)
                    .where(Booking.type.in_(["personal"]))
                )
                user_booked_dates = [row[0] for row in user_bookings_result.all()]
                # 2. Получаем общее количество бронирований для каждой даты
                bookings_count_result = await session.execute(
                    select(Booking.booking_date, func.count(Booking.id))
                    .where(Booking.type.in_(["personal", "guest"]))
                    .group_by(Booking.booking_date)
                )
                bookings_count_by_date = {
                    date: count for date, count in bookings_count_result.all()
                }
            except Exception:
                await session.rollback()
                raise ValueError

        available_dates = []

        for date in upcoming_dates:
            date_obj = date["date_obj"]

            # 1. Отбрасываем даты, на которые у пользователя уже есть бронирование
            if date_obj in user_booked_dates:
                continue

            # 2. Отбрасываем даты с "максимальным" количеством бронирований
            booking_count = bookings_count_by_date.get(date_obj, 0)
            if booking_count >= max_bookings_per_day:
                continue

            # Если дата прошла оба фильтра, добавляем в доступные
            available_dates.append(date)

        return available_dates

    @staticmethod
    async def get_dates_wo_user_bookings(tg_id: int) -> list[dict]:
        """
        Получить даты на 14 дней вперед доступные для посещения офиса (не бронирования места)
        с учетом уже созданных персональных бронирований пользователя.
        """
        upcoming_dates = await utils.generate_upcoming_dates()

        # Получаем даты, на которые у пользователя уже есть персональные бронирования
        user_booked_dates = []

        async for session in get_db_session():
            try:
                stmt = (
                    select(Booking.booking_date)
                    .join(User, User.id == Booking.user_id)
                    .where(User.tg_id == tg_id)
                    .where(Booking.type.in_(["personal", "personal_candidate"]))
                )
                result = await session.execute(stmt)
                user_booked_dates = [row[0] for row in result.all()]

            except Exception:
                await session.rollback()
                raise ValueError

        available_dates = []

        for date in upcoming_dates:
            date_obj = date["date_obj"]

            # Отбрасываем даты, на которые у пользователя уже есть бронирование
            if date_obj in user_booked_dates:
                continue

            # Если дата прошла оба фильтра, добавляем в доступные
            available_dates.append(date)

        return available_dates

    @staticmethod
    async def get_guest_available_dates() -> list[dict]:
        """
        Получить даты доступные для гостевого бронирования места
        с учетом только заполненности офиса.
        """
        upcoming_dates = await utils.generate_upcoming_dates()
        max_bookings_per_day = len(settings.EXISTING_SEATS_LIST)

        # Получаем общее количество бронирований на каждую дату
        bookings_count_by_date = {}

        async for session in get_db_session():
            try:
                # Получаем общее количество бронирований для каждой даты
                bookings_count_result = await session.execute(
                    select(Booking.booking_date, func.count(Booking.id))
                    .where(Booking.type.in_(["personal", "guest"]))
                    .group_by(Booking.booking_date)
                )
                bookings_count_by_date = {
                    date: count for date, count in bookings_count_result.all()
                }
            except Exception:
                await session.rollback()
                raise ValueError

        available_dates = []

        for date in upcoming_dates:
            date_obj = date["date_obj"]

            # Отбрасываем даты с максимальным количеством бронирований
            booking_count = bookings_count_by_date.get(date_obj, 0)
            if booking_count >= max_bookings_per_day:
                continue

            # Если дата прошла оба фильтра, добавляем в доступные
            available_dates.append(date)

        return available_dates

    @staticmethod
    async def get_available_seats(book_date: str) -> list[str]:
        """Получить места доступные для бронирования на дату."""
        book_date_obj = datetime.datetime.strptime(book_date, "%Y-%m-%d").date()
        async for session in get_db_session():
            try:
                # Находим все забронированные места на выбранную дату
                result = await session.execute(
                    select(Booking.seat_number).where(
                        Booking.booking_date == book_date_obj,
                        Booking.seat_number.isnot(None),
                    )
                )
                occupied_seats = result.scalars().all()

                if len(occupied_seats) == len(settings.EXISTING_SEATS_LIST):
                    raise ValueError(f"Свободных мест нет на выбранную дату.")

                available_seats = [
                    seat
                    for seat in settings.EXISTING_SEATS_LIST
                    if seat not in occupied_seats
                ]

                return available_seats

            except Exception:
                await session.rollback()
                raise ValueError

    @staticmethod
    async def create_booking(
        *,
        booking_date: datetime.date,
        user_id: int,
        seat_number: str | None,
        booking_type: str,
        guest_full_name: str | None,
    ) -> Booking:
        """Создать бронирование."""
        async for session in get_db_session():
            try:
                if seat_number:
                    # Проверка, что место на дату еще свободно
                    existing = await session.execute(
                        select(Booking.id).where(
                            Booking.booking_date == booking_date,
                            Booking.seat_number == seat_number,
                        )
                    )
                    if existing.scalar_one_or_none():
                        raise BookingConflictError

                booking = Booking(
                    booking_date=booking_date,
                    user_id=user_id,
                    seat_number=seat_number,
                    type=booking_type,
                    guest_full_name=guest_full_name,
                )
                session.add(booking)
                await session.commit()
                await session.refresh(booking)

                return booking

            except IntegrityError:
                await session.rollback()
                raise BookingConflictError

    @staticmethod
    async def delete_booking(booking_id: int) -> Booking:
        """Удалить бронирование."""
        async for session in get_db_session():
            try:
                result = await session.execute(
                    select(Booking).where(Booking.id == booking_id)
                )
                booking = result.scalar_one_or_none()

                # Удаляем объект
                await session.delete(booking)
                await session.commit()

                return booking

            except Exception:
                await session.rollback()
                raise ValueError

    @staticmethod
    async def get_user_future_bookings(user_id: int) -> list[Booking]:
        """Получить данные всех бронирований пользователя."""
        current_date_obj = datetime.datetime.strptime(
            utils.get_current_timestamp().split(" ")[0], "%Y-%m-%d"
        ).date()
        async for session in get_db_session():
            try:
                result = await session.execute(
                    select(Booking)
                    .where(Booking.user_id == user_id)
                    .where(Booking.booking_date >= current_date_obj)
                    .order_by(Booking.booking_date)
                )
                user_bookings = result.scalars().all()

                return user_bookings

            except Exception:
                await session.rollback()
                raise ValueError

    @staticmethod
    async def get_all_future_bookings() -> list[dict]:
        """Получить данные всех будущих бронирований всех пользователей."""
        current_date_obj = datetime.datetime.strptime(
            utils.get_current_timestamp().split(" ")[0], "%Y-%m-%d"
        ).date()
        async for session in get_db_session():
            try:
                bookings = (
                    select(
                        Booking.id,
                        Booking.booking_date,
                        Booking.guest_full_name,
                        User.full_name,
                        Booking.seat_number,
                        Booking.type,
                    )
                    .join(User, User.id == Booking.user_id)
                    .where(Booking.booking_date >= current_date_obj)
                    .order_by(Booking.booking_date)
                )

                result = await session.execute(bookings)
                rows = (
                    result.all()
                )  # список кортежей (id, seat_number, type, guest_full_name, full_name)

                # Преобразуем в список словарей для удобства
                # Берем ФИО гостя, если есть, если нет - ФИО владельца брони
                return [
                    {
                        "booking_id": r[0],
                        "booking_date": r[1],
                        "full_name": r[2] if r[2] else r[3],
                        "seat_number": r[4],
                        "type": r[5],
                    }
                    for r in rows
                ]

            except Exception:
                await session.rollback()
                raise ValueError

    @staticmethod
    async def get_dates_with_visitors() -> list[datetime.date]:
        """
        Получить список уникальных дат на которые
        есть хотя бы одно бронирование от любого из сотрудников.
        """
        async for session in get_db_session():
            try:
                # Получаем текущую дату для фильтрации будущих бронирований
                current_date_obj = datetime.datetime.strptime(
                    utils.get_current_timestamp().split(" ")[0], "%Y-%m-%d"
                ).date()

                # Выбираем уникальные даты бронирований, которые сегодня или в будущем
                result = await session.execute(
                    select(Booking.booking_date)
                    .where(Booking.booking_date >= current_date_obj)
                    .distinct()
                    .order_by(Booking.booking_date)
                )

                dates = result.scalars().all()

                return dates

            except Exception:
                await session.rollback()
                raise ValueError

    @staticmethod
    async def get_visitors_by_date(date: datetime.date) -> list[dict]:
        """
        Получить данные всех бронирований пользователей на дату:
        seat_number + full_name + type + guest_full_name.
        """
        async for session in get_db_session():
            try:
                bookings = (
                    select(
                        Booking.seat_number,
                        Booking.type,
                        Booking.guest_full_name,
                        User.full_name,
                    )
                    .join(User, User.id == Booking.user_id)
                    .where(Booking.booking_date == date)
                    .order_by(Booking.seat_number)
                )

                result = await session.execute(bookings)
                rows = (
                    result.all()
                )  # список кортежей (seat_number, type, guest_full_name, full_name)

                # Преобразуем в список словарей для удобства
                # Берем ФИО гостя, если есть, если нет - ФИО владельца брони
                return [
                    {
                        "seat_number": r[0],
                        "type": r[1],
                        "full_name": r[2] if r[2] else r[3],
                    }
                    for r in rows
                ]

            except Exception:
                await session.rollback()
                raise ValueError

    @staticmethod
    async def cleanup_old_bookings(days: int = 90) -> int:
        """
        Удаляет бронирования старше N дней.
        Возвращает количество удалённых записей.
        """
        cutoff_date = datetime.datetime.now(
            ZoneInfo("Europe/Moscow")
        ).date() - datetime.timedelta(days=days)

        async for session in get_db_session():
            try:
                result = await session.execute(
                    delete(Booking)
                    .where(Booking.booking_date < cutoff_date)
                    .returning(Booking.id)
                )
                deleted_rows = result.fetchall()
                await session.commit()
                return len(deleted_rows), str(cutoff_date)

            except Exception:
                await session.rollback()
                raise
