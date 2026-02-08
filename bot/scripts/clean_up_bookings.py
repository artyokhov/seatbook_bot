import asyncio
import logging

from config.logging_config import setup_logging
from services.booking_service import BookingService

setup_logging()

logger = logging.getLogger("seatbook")


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
