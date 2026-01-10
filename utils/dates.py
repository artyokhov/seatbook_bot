import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

from config.settings import settings

# Русские названия месяцев
months_ru = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}

# Русские названия дней недели
weekdays_ru = {
    0: "понедельник",
    1: "вторник",
    2: "среда",
    3: "четверг",
    4: "пятница",
    5: "суббота",
    6: "воскресенье",
}


async def generate_upcoming_dates() -> list[dict]:
    """Генерирует список дат на количество дней планирования вперед от сегодняшней даты включительно."""
    today = datetime.date.today()
    dates_list = []
    planning_days = settings.PLANNING_DAYS

    for i in range(planning_days):
        current_date = today + timedelta(days=i)
        day = current_date.day
        month = months_ru[current_date.month]
        weekday = weekdays_ru[current_date.weekday()]

        formatted_date = f"{day} {month}, {weekday}"
        timestamp = current_date.isoformat()  # Формат: YYYY-MM-DD

        dates_list.append(
            {
                "formatted": formatted_date,
                "timestamp": str(timestamp),
                "date_obj": current_date,
            }
        )

    return dates_list


def get_current_timestamp() -> str:
    """Возвращает текущую дату и время в формате строки ISO 8601 в UTC+3."""
    MOSCOW_TZ = ZoneInfo("Europe/Moscow")
    return datetime.datetime.now(MOSCOW_TZ).isoformat(sep=" ", timespec="seconds")


def format_booking_date(date_obj: datetime.date) -> str:
    """Преобразует дату ISO 8601 вида "2025-05-13" в дату вида "13 мая, среда"."""

    day = date_obj.day
    month = months_ru[date_obj.month]
    weekday = weekdays_ru[date_obj.weekday()]

    return f"{day} {month}, {weekday}"


def format_dates_list(dates: list[datetime.date]) -> list[dict]:
    """Преобразует список строк с датами в список словарей с отформатированными данными."""
    dates_list = []

    for date in dates:

        # Форматируем дату используя существующую функцию
        formatted_date = format_booking_date(date)

        # Добавляем в список
        dates_list.append(
            {
                "formatted": formatted_date,
                "timestamp": str(date.isoformat()),
                "date_obj": date,
            }
        )

    return dates_list
