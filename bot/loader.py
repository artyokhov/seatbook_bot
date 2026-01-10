# bot/loader.py
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage

from config.settings import settings

# Используем StateMemoryStorage, в будущем можно перейти на Redis
storage = StateMemoryStorage()

bot = AsyncTeleBot(settings.BOT_TOKEN, state_storage=storage, parse_mode="HTML")
