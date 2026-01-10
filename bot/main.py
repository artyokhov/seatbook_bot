import asyncio

import handlers
from bot.dependencies import logger
from bot.loader import bot
from scripts.preload_images import preload_images


async def main():
    await preload_images()
    print("Бот запущен...", flush=True)
    await bot.infinity_polling()


if __name__ == "__main__":
    asyncio.run(main())
