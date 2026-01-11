import asyncio

from bot.dependencies import logger
from services.booking_service import BookingService


async def main():
    deleted, cutoff_date = await BookingService.cleanup_old_bookings(days=90)
    logger.info(
        f"Система удалила {str(deleted)} бронирований с датой раньше чем {str(cutoff_date)}"
    )
    print(
        f"Система удалила {str(deleted)} бронирований с датой раньше чем {str(cutoff_date)}",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
