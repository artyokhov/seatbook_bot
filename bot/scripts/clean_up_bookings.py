import asyncio

from bot.dependencies import logger
from services.booking_service import BookingService


async def main():
    deleted, cutoff_date = await BookingService.cleanup_old_bookings(days=90)
    logger.info(
        "Система удалила %s бронирований с датой раньше чем %s",
        deleted,
        cutoff_date,
    )
    print(
        f"Система удалила {deleted} бронирований с датой раньше чем {cutoff_date}",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
