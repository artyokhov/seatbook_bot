import logging

from telebot.types import CallbackQuery, Message

import keyboards
import messages
import utils
from bot import bot, logger
from config.settings import settings
from scripts.preload_images import preload_images, preloaded_images
from services import BookingService, UserService

from . import decorators


@decorators.error_query_handler
@decorators.admin_required
@bot.callback_query_handler(lambda query: query.data == "admin_options")
async def handle_admin_options_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека панели администратора ("admin_options")
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)

        await bot.send_message(
            query.message.chat.id,
            text=messages.admin_options_text,
            reply_markup=keyboards.admin_options_markup,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )

    except Exception as e:
        error_caption = messages.prepare_error_caption(e)
        logger.error(
            "Unexpected error",
            exc_info=True,
        )
        await bot.send_message(
            query.message.chat.id,
            text=messages.error_w_caption_text.format(error_caption=error_caption),
            reply_markup=keyboards.to_start_markup,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )


@decorators.error_query_handler
@decorators.admin_required
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("users_w_tg_id_page:")
)
async def handle_users_w_tg_id_page_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса списка ФИО сотрудников,
    с привязанным tg_id, т.е. зарегистрированные сотрудники
    ("users_w_tg_id_page: page")
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        required_page = int(
            query.data.split(":")[1].strip()
        )  # Получаем номер требуемой страницы из callback_data
        users_w_tg_id = await UserService.get_users_w_tg_id(page=required_page)
        selection_keyboard = keyboards.name_w_tg_id_selection_markup(
            users_w_tg_id["users"], users_w_tg_id["page"], users_w_tg_id["total_pages"]
        )
        await bot.send_message(
            query.message.chat.id,
            text=messages.users_w_tg_id_page_selection_text,
            reply_markup=selection_keyboard,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )

    except Exception as e:
        error_caption = messages.prepare_error_caption(e)
        logger.error(
            "Unexpected error",
            exc_info=True,
        )
        await bot.send_message(
            query.message.chat.id,
            text=messages.error_w_caption_text.format(error_caption=error_caption),
            reply_markup=keyboards.to_start_markup,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )


@decorators.error_query_handler
@decorators.admin_required
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("untie_warn: ")
)
async def handle_untie_warn_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса на отвязку ФИО от tg_id,
    возвращает предупрежедение, не выполняет отвязку
    ("untie_warn: user_id")
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        user_id = int(query.data.split(":")[1].strip())
        user_data = await UserService.get_user_by_user_id(user_id)
        full_name = user_data.full_name

        await bot.send_message(
            query.message.chat.id,
            text=messages.untie_warn_text.format(full_name=full_name),
            reply_markup=keyboards.untie_warn_markup(user_id),
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )

    except Exception as e:
        error_caption = messages.prepare_error_caption(e)
        logger.error(
            "Unexpected error",
            exc_info=True,
        )
        await bot.send_message(
            query.message.chat.id,
            text=messages.error_w_caption_text.format(error_caption=error_caption),
            reply_markup=keyboards.to_start_markup,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )


@decorators.error_query_handler
@decorators.admin_required
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("untie_make: ")
)
async def handle_untie_make_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека выполнения отвязки ФИО от tg_id,
    удаляет все бронирования пользователя и обнуляет tg_id, chat_id, username в таблице users
    ("untie_make: user_id")
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        user_id = int(query.data.split(":")[1].strip())
        user = await UserService.get_user_by_user_id(user_id)
        full_name = user.full_name

        # Отвязываем пользователя
        await UserService.untie_user_tg_id(user_id=user_id)
        logger.info("%s отвязал tg_id у %s", query.from_user.username, full_name)
        await bot.send_message(
            query.message.chat.id,
            text=messages.untie_success_text,
            reply_markup=keyboards.to_start_markup,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )

    except Exception as e:
        error_caption = messages.prepare_error_caption(e)
        logger.error(
            "Unexpected error",
            exc_info=True,
        )
        await bot.send_message(
            query.message.chat.id,
            text=messages.error_w_caption_text.format(error_caption=error_caption),
            reply_markup=keyboards.to_start_markup,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )


@decorators.error_query_handler
@decorators.admin_required
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("delete_user_page: ")
)
async def handle_delete_user_page_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса списка ФИО сотрудников для удаления из системы
    ("delete_user_page: page")
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        required_page = int(
            query.data.split(":")[1].strip()
        )  # Получаем номер требуемой страницы из callback_data
        all_fullnames = await UserService.get_all_fullnames(page=required_page)
        selection_keyboard = keyboards.fullnames_selection_markup(
            all_fullnames["users"], all_fullnames["page"], all_fullnames["total_pages"]
        )
        await bot.send_message(
            query.message.chat.id,
            text=messages.delete_page_selection_text,
            reply_markup=selection_keyboard,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )

    except Exception as e:
        error_caption = messages.prepare_error_caption(e)
        logger.error(
            "Unexpected error",
            exc_info=True,
        )
        await bot.send_message(
            query.message.chat.id,
            text=messages.error_w_caption_text.format(error_caption=error_caption),
            reply_markup=keyboards.to_start_markup,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )


@decorators.error_query_handler
@decorators.admin_required
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("delete_warn: ")
)
async def handle_delete_warn_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса на удаление ФИО из системы,
    возвращает предупреждение, не выполняет удаление
    ("delete_warn: user_id")
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        user_id = int(query.data.split(":")[1].strip())
        user_data = await UserService.get_user_by_user_id(user_id)
        full_name = user_data.full_name

        await bot.send_message(
            query.message.chat.id,
            text=messages.delete_warn_text.format(full_name=full_name),
            reply_markup=keyboards.delete_warn_markup(user_id),
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )

    except Exception as e:
        error_caption = messages.prepare_error_caption(e)
        logger.error(
            "Unexpected error",
            exc_info=True,
        )
        await bot.send_message(
            query.message.chat.id,
            text=messages.error_w_caption_text.format(error_caption=error_caption),
            reply_markup=keyboards.to_start_markup,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )


@decorators.error_query_handler
@decorators.admin_required
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("delete_make: ")
)
async def handle_delete_make_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека выполнения удаления ФИО из системы,
    удаляет все бронирования пользователя и удаляет запись из таблицы users
    ("delete_make: user_id")
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        user_id = int(query.data.split(":")[1].strip())
        user = await UserService.get_user_by_user_id(user_id)
        full_name, username = user.full_name, user.username

        # Удаляем пользователя
        await UserService.delete_user(user_id=user_id)
        logger.info(
            "%s удалил из системы пользователя %s %s",
            query.from_user.username,
            full_name,
            username,
        )
        await bot.send_message(
            query.message.chat.id,
            text=messages.delete_success_text,
            reply_markup=keyboards.to_start_markup,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )

    except Exception as e:
        error_caption = messages.prepare_error_caption(e)
        logger.error(
            "Unexpected error",
            exc_info=True,
        )
        await bot.send_message(
            query.message.chat.id,
            text=messages.error_w_caption_text.format(error_caption=error_caption),
            reply_markup=keyboards.to_start_markup,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )


@decorators.error_query_handler
@decorators.admin_required
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("add_user")
)
async def handle_add_user_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса интерфейса ввода ФИО нового сотрудника
    ("add_user")
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)

        # Предлагаем ввести ФИО
        await bot.send_message(
            query.message.chat.id,
            text=messages.new_user_name_forcereply_text,
            reply_markup=keyboards.name_forcereply_markup,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )

    except Exception as e:
        error_caption = messages.prepare_error_caption(e)
        logger.error(
            "Unexpected error",
            exc_info=True,
        )
        await bot.send_message(
            query.message.chat.id,
            text=messages.error_w_caption_text.format(error_caption=error_caption),
            reply_markup=keyboards.to_start_markup,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )


@decorators.error_command_handler
@decorators.admin_required
@bot.message_handler(
    func=lambda message: message.reply_to_message
    and message.reply_to_message.text.startswith("Введите ФИО нового сотрудника")
)
async def handle_new_user_input(message: Message) -> None:
    """
    Обработчик сообщения с введенным ФИО нового сотрудника
    (удаляет "сообщение с ФИО сотрудника" сразу и
    создает запись в таблице users с ФИО)
    """
    try:
        full_name = message.text.strip()
        if not utils.is_full_name(full_name):
            await bot.send_message(
                message.chat.id,
                text=messages.error_invalid_full_name_text,
                reply_markup=keyboards.to_start_markup,
            )
            await bot.delete_message(message.chat.id, message.message_id, timeout=1)
            return

        # Создаем сотрудника
        new_user = await UserService.add_user(full_name=full_name)
        logger.info("%s добавил пользователя %s", message.from_user.username, full_name)
        if message.reply_to_message:
            try:
                await bot.delete_message(
                    message.chat.id, message.reply_to_message.message_id
                )
            except Exception as e:
                print(f"Не удалось удалить исходное сообщение: {e}", flush=True)

        await bot.send_message(
            message.chat.id,
            text=messages.new_user_success_text.format(full_name=new_user.full_name),
            reply_markup=keyboards.to_start_markup,
        )
        await bot.delete_message(message.chat.id, message.message_id, timeout=1)

    except Exception as e:
        error_caption = messages.prepare_error_caption(e)
        logger.error(
            "Unexpected error",
            exc_info=True,
        )
        await bot.send_message(
            message.chat.id,
            text=messages.error_w_caption_text.format(error_caption=error_caption),
            reply_markup=keyboards.to_start_markup,
        )
        await bot.delete_message(message.chat.id, message.message_id, timeout=1)


@decorators.error_query_handler
@decorators.admin_required
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("see_all_bookings")
)
async def handle_see_all_bookings_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека "посмотреть все будущие бронирования" ("see_all_bookings")
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)

        bookings = await BookingService.get_all_future_bookings()
        if bookings:
            bookings_text = messages.future_bookings_list_header
            for booking in bookings:
                booking_date = utils.format_booking_date(booking["booking_date"])
                booking_type = utils.get_booking_type_name(booking["type"])
                seat_number = booking["seat_number"] if booking["seat_number"] else "XX"
                full_name = (
                    booking["full_name"]
                    if booking["full_name"]
                    else booking["guest_full_name"]
                )
                booking_id = booking["booking_id"]
                bookings_text += messages.future_bookings_list_item.format(
                    booking_id=booking_id,
                    booking_date=booking_date,
                    seat=seat_number,
                    booking_type=booking_type,
                    full_name=full_name,
                )
        else:
            bookings_text = messages.no_future_booking_text

        text_chunks = utils.split_bookings_html_by_b_tags(
            bookings_text,
            bookings_ids=(
                [booking["booking_id"] for booking in bookings] if bookings else []
            ),
        )
        for text in text_chunks:
            await bot.send_message(
                query.message.chat.id,
                text=text["text_part"],
                reply_markup=(
                    keyboards.delete_booking_by_id_markup(text["bookings_ids"])
                    if bookings
                    else keyboards.to_start_markup
                ),
            )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )

    except Exception as e:
        error_caption = messages.prepare_error_caption(e)
        logger.error(
            "Unexpected error",
            exc_info=True,
        )
        await bot.send_message(
            query.message.chat.id,
            text=messages.error_w_caption_text.format(error_caption=error_caption),
            reply_markup=keyboards.to_start_markup,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )


@decorators.error_query_handler
@bot.callback_query_handler(func=lambda query: True)
async def handle_unknown_query(query: CallbackQuery) -> None:
    """
    Обработчик неопознанного коллбека --- IGNORE ---
    (важно чтобы он присутствовал в ПОСЛЕДНЕМ импортиуремом
    в main.py модуле, иначе он будет ловить корреткные коллбеки).
    Нужно для отладки при добавлении новых коллбеков или хэндлер-модулей
    """
    print("Неопознанный колбэк: ", query.data, flush=True)
    error_caption = "Неопознанный колбэк: " + f" {query.data}"
    logger.error(
        "Unexpected callback",
        exc_info=True,
    )
    await bot.send_message(
        query.message.chat.id,
        text=messages.error_w_caption_text.format(error_caption=error_caption),
        reply_markup=keyboards.to_start_markup,
    )
    await bot.delete_message(query.message.chat.id, query.message.message_id, timeout=1)
