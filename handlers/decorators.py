from functools import wraps

import keyboards
import messages
import utils
from bot import bot, logger
from config.settings import settings
from services.errors import BookingConflictError


def error_command_handler(func):
    """Декоратор для обработки ошибок в командах бота."""

    @wraps(func)
    async def wrap_function(message):
        result = None
        try:
            result = await func(message)
        except Exception as e:
            error_caption = messages.prepare_error_caption(e)
            logger.error(
                "Unexpected error",
                exc_info=True,
            )

            # await bot.send_message(
            #     message.chat.id,
            #     text=messages.error_w_caption_text.format(error_caption=error_caption),
            #     reply_markup=keyboards.to_start_markup,
            # )
            # await bot.delete_message(message.chat.id, message.message_id, timeout=1)
            await utils.safely_replace_message(
                message,
                new_message_type=utils.MessageContentType.TEXT,
                new_text=messages.error_w_caption_text.format(
                    error_caption=error_caption
                ),
                new_reply_markup=keyboards.to_start_markup,
            )
            print("Ошибка: ", type(e).__name__, e)

        return result

    return wrap_function


def error_query_handler(func):
    """Декоратор для обработки ошибок в колбеках бота."""

    @wraps(func)
    async def wrap_function(query):
        result = None
        try:
            result = await func(query)
        except Exception as e:
            error_caption = messages.prepare_error_caption(e)
            logger.error(
                "Unexpected error",
                exc_info=True,
            )
            # await bot.send_message(
            #     query.message.chat.id,
            #     text=messages.error_w_caption_text.format(error_caption=error_caption),
            #     reply_markup=keyboards.to_start_markup,
            # )
            # await bot.delete_message(
            #     query.message.chat.id, query.message.message_id, timeout=1
            # )
            await utils.safely_replace_message(
                query,
                new_message_type=utils.MessageContentType.TEXT,
                new_text=messages.error_w_caption_text.format(
                    error_caption=error_caption
                ),
                new_reply_markup=keyboards.to_start_markup,
            )
            print("Ошибка: ", type(e).__name__, e)

        return result

    return wrap_function


def admin_required(func):
    """Декоратор для проверки прав администратора."""

    @wraps(func)
    async def wrap_function(query, *args, **kwargs):
        if query.from_user.username not in settings.ADMIN_USERNAMES_LIST:
            await bot.answer_callback_query(query.id)
            await bot.delete_message(query.message.chat.id, query.message.message_id)
            await bot.send_message(
                query.message.chat.id,
                text="Вы не являетесь администратором",
                reply_markup=keyboards.to_start_markup,
            )
            return
        return await func(query, *args, **kwargs)

    return wrap_function
