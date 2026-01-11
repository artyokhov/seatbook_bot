from telebot.types import CallbackQuery, Message

import keyboards
import messages
import utils
from bot import bot, logger
from services import BookingService, UserService

from . import decorators


@bot.callback_query_handler(lambda query: query.data == "admin_options")
@decorators.error_query_handler
@decorators.admin_required
async def handle_admin_options_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека панели администратора ("admin_options")
    """
    await bot.answer_callback_query(callback_query_id=query.id)

    await utils.safely_replace_message(
        query,
        new_message_type=utils.MessageContentType.TEXT,
        new_text=messages.admin_options_text,
        new_reply_markup=keyboards.admin_options_markup,
    )


@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("users_w_tg_id_page:")
)
@decorators.error_query_handler
@decorators.admin_required
async def handle_users_w_tg_id_page_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса списка ФИО сотрудников,
    с привязанным tg_id, т.е. ФИО зарегистрированных сотрудников
    ("users_w_tg_id_page: page")
    """
    await bot.answer_callback_query(callback_query_id=query.id)
    required_page = int(
        query.data.split(":")[1].strip()
    )  # Получаем номер требуемой страницы из callback_data
    users_w_tg_id = await UserService.get_users_w_tg_id(page=required_page)
    selection_keyboard = keyboards.name_w_tg_id_selection_markup(
        users_w_tg_id["users"], users_w_tg_id["page"], users_w_tg_id["total_pages"]
    )

    await utils.safely_replace_message(
        query,
        new_message_type=utils.MessageContentType.TEXT,
        new_text=messages.users_w_tg_id_page_selection_text,
        new_reply_markup=selection_keyboard,
    )


@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("untie_warn: ")
)
@decorators.error_query_handler
@decorators.admin_required
async def handle_untie_warn_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса на отвязку ФИО от tg_id,
    возвращает предупрежедение, не выполняет отвязку
    ("untie_warn: user_id")
    """
    await bot.answer_callback_query(callback_query_id=query.id)
    user_id = int(query.data.split(":")[1].strip())
    user_data = await UserService.get_user_by_user_id(user_id)
    full_name = user_data.full_name

    await utils.safely_replace_message(
        query,
        new_message_type=utils.MessageContentType.TEXT,
        new_text=messages.untie_warn_text.format(full_name=full_name),
        new_reply_markup=keyboards.untie_warn_markup(user_id),
    )


@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("untie_make: ")
)
@decorators.error_query_handler
@decorators.admin_required
async def handle_untie_make_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека выполнения отвязки ФИО от tg_id,
    удаляет все бронирования пользователя и обнуляет tg_id, chat_id, username в таблице users
    ("untie_make: user_id")
    """
    await bot.answer_callback_query(callback_query_id=query.id)
    user_id = int(query.data.split(":")[1].strip())
    user = await UserService.get_user_by_user_id(user_id)
    full_name = user.full_name

    # Отвязываем пользователя
    await UserService.untie_user_tg_id(user_id=user_id)
    logger.info("%s отвязал tg_id у %s", query.from_user.username, full_name)

    await utils.safely_replace_message(
        query,
        new_message_type=utils.MessageContentType.TEXT,
        new_text=messages.untie_success_text,
        new_reply_markup=keyboards.to_start_markup,
    )


@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("delete_user_page: ")
)
@decorators.error_query_handler
@decorators.admin_required
async def handle_delete_user_page_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса списка ФИО сотрудников для удаления из системы
    ("delete_user_page: page")
    """
    await bot.answer_callback_query(callback_query_id=query.id)
    required_page = int(
        query.data.split(":")[1].strip()
    )  # Получаем номер требуемой страницы из callback_data
    all_fullnames = await UserService.get_all_fullnames(page=required_page)
    selection_keyboard = keyboards.fullnames_selection_markup(
        all_fullnames["users"], all_fullnames["page"], all_fullnames["total_pages"]
    )

    await utils.safely_replace_message(
        query,
        new_message_type=utils.MessageContentType.TEXT,
        new_text=messages.delete_page_selection_text,
        new_reply_markup=selection_keyboard,
    )


@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("delete_warn: ")
)
@decorators.error_query_handler
@decorators.admin_required
async def handle_delete_warn_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса на удаление ФИО из системы,
    возвращает предупреждение, не выполняет удаление
    ("delete_warn: user_id")
    """
    await bot.answer_callback_query(callback_query_id=query.id)
    user_id = int(query.data.split(":")[1].strip())
    user_data = await UserService.get_user_by_user_id(user_id)
    full_name = user_data.full_name

    await utils.safely_replace_message(
        query,
        new_message_type=utils.MessageContentType.TEXT,
        new_text=messages.delete_warn_text.format(full_name=full_name),
        new_reply_markup=keyboards.delete_warn_markup(user_id),
    )


@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("delete_make: ")
)
@decorators.error_query_handler
@decorators.admin_required
async def handle_delete_make_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека выполнения удаления ФИО из системы,
    удаляет все бронирования пользователя и удаляет запись из таблицы users
    ("delete_make: user_id")
    """
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

    await utils.safely_replace_message(
        query,
        new_message_type=utils.MessageContentType.TEXT,
        new_text=messages.delete_success_text,
        new_reply_markup=keyboards.to_start_markup,
    )


@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("add_user")
)
@decorators.error_query_handler
@decorators.admin_required
async def handle_add_user_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса интерфейса ввода ФИО нового сотрудника
    ("add_user")
    """
    await bot.answer_callback_query(callback_query_id=query.id)

    await utils.safely_replace_message(
        query,
        new_message_type=utils.MessageContentType.TEXT,
        new_text=messages.new_user_name_forcereply_text,
        new_reply_markup=keyboards.name_forcereply_markup,
    )


@bot.message_handler(
    func=lambda message: message.reply_to_message
    and message.reply_to_message.text.startswith("Введите ФИО нового сотрудника")
)
@decorators.error_query_handler
@decorators.admin_required
async def handle_new_user_input(message: Message) -> None:
    """
    Обработчик сообщения с введенным ФИО нового сотрудника
    (удаляет "сообщение с ФИО сотрудника" сразу и
    создает запись в таблице users с ФИО)
    """
    full_name = message.text.strip()
    if not utils.is_full_name(full_name):

        await utils.safely_replace_message(
            message,
            new_message_type=utils.MessageContentType.TEXT,
            new_text=messages.error_invalid_full_name_text,
            new_reply_markup=keyboards.to_start_markup,
        )
        return

    # Создаем сотрудника
    new_user = await UserService.add_user(full_name=full_name)
    logger.info("%s добавил пользователя %s", message.from_user.username, full_name)
    if message.reply_to_message:
        await utils.safely_delete_message(
            message.chat.id, message.reply_to_message.message_id
        )

    await utils.safely_replace_message(
        message,
        new_message_type=utils.MessageContentType.TEXT,
        new_text=messages.new_user_success_text.format(full_name=new_user.full_name),
        new_reply_markup=keyboards.to_start_markup,
    )


@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("see_all_bookings")
)
@decorators.error_query_handler
@decorators.admin_required
async def handle_see_all_bookings_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека "посмотреть все будущие бронирования" ("see_all_bookings")
    """
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
    await utils.safely_delete_message(query.message.chat.id, query.message.message_id)


@bot.callback_query_handler(func=lambda query: True)
@decorators.error_query_handler
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
    await utils.safely_delete_message(query.message.chat.id, query.message.message_id)
