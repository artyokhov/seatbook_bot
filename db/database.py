import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config.settings import settings

# Создаем движок и фабрику сессий
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
print("DB URL in use: ", settings.DATABASE_URL)

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()


# Функция для получения сессии (будет использоваться в сервисах)
async def get_db_session():
    """Асинхронный контекстный менеджер для работы с сессией БД."""
    async with AsyncSessionLocal() as session:
        yield session
