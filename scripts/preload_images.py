import asyncio
import os

from telebot.async_telebot import AsyncTeleBot

from config.settings import settings

# ⚠️ Здесь можно сделать так: бот загружает картинку в твой ADMIN_USERNAMES[0]
BOT = AsyncTeleBot(settings.BOT_TOKEN)

# Хранилище для file_id
preloaded_images = {}


async def preload_images():
    """
    Загружает изображения при старте и сохраняет их file_id для дальнейшего использования.
    """
    office_map_path = settings.OFFICE_MAP_PATH

    if not os.path.exists(office_map_path):
        print(f"⚠️ Image not found: {office_map_path}")
        return

    print(f"📤 Uploading office map {office_map_path} to Telegram...")

    # Отправляем в личку главному единственному админу (или можно настроить в скрытый служебный канал, нужен именно ID)
    msg = await BOT.send_photo(
        settings.ADMIN_CHAT_ID,
        photo=open(office_map_path, "rb"),
        caption="Карта мест загружена.",
    )

    # Берем file_id самого большого размера фото
    file_id = msg.photo[-1].file_id
    preloaded_images["office_map"] = file_id

    print(f"✅ Office map preloaded with file_id: {file_id}")
