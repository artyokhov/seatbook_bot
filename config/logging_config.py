import logging
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfo

from . import settings

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class OnlyInfoFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == logging.INFO


class MoscowFormatter(logging.Formatter):
    tz = ZoneInfo("Europe/Moscow")

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=self.tz)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def setup_logging():
    logger = logging.getLogger("seatbook")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = MoscowFormatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    # Бизнес-события
    events_handler = TimedRotatingFileHandler(
        LOG_DIR / "events.log",
        when="D",
        interval=1,
        backupCount=30,  # хранить 30 дней
        encoding="utf-8",
    )
    events_handler.setLevel(logging.INFO)
    events_handler.addFilter(OnlyInfoFilter())
    events_handler.setFormatter(formatter)

    # Ошибки
    errors_handler = TimedRotatingFileHandler(
        LOG_DIR / "errors.log",
        when="D",
        interval=1,
        backupCount=30,  # хранить 30 дней
        encoding="utf-8",
    )
    errors_handler.setLevel(logging.ERROR)
    errors_handler.setFormatter(formatter)

    logger.addHandler(events_handler)
    logger.addHandler(errors_handler)

    # Логгер для библиотеки Telebot
    for name in ("telebot", "telebot.async_telebot", "TeleBot"):
        tb_logger = logging.getLogger(name)
        tb_logger.setLevel(logging.ERROR)
        tb_logger.handlers.clear()
        tb_logger.addHandler(errors_handler)
        tb_logger.propagate = False

    return logger
