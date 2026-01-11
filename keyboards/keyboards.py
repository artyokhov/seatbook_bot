from telebot import util
from telebot.types import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup

from db.models import User


def name_selection_markup(
    free_users: list[User], page: int = 0, total_pages: int = 0
) -> InlineKeyboardMarkup:
    """Создать на основе списка пользователей, информации о текущей странице и всего страницах клавиатуру с ФИО свободных пользователей"""

    # Создаем кнопки с ФИО
    buttons = {}
    for user in free_users:
        user_id = user.id
        full_name = user.full_name
        button = {"callback_data": f"reg: {user_id}"}
        buttons[full_name] = button

    # Создаем кнопки навигации по страницам
    pagination_buttons = {}

    if total_pages > 1:
        if page > 0:
            pagination_buttons["◀️ Назад"] = {"callback_data": f"users_page: {page - 1}"}

        if page < total_pages - 1:
            pagination_buttons["Вперед ▶️"] = {
                "callback_data": f"users_page: {page + 1}"
            }

    all_buttons = {**buttons, **pagination_buttons}

    return util.quick_markup(all_buttons, row_width=2)


def confirm_registration_markup(user_id: int) -> InlineKeyboardMarkup:
    """
    Создать клавиатуру для подтверждения регистрации пользователя с выбранным ФИО
    """
    return util.quick_markup(
        {
            "🟢 Да, верно": {"callback_data": f"cnfm_reg: {user_id}"},
            "↩️ Нет, выбрать другое имя": {"callback_data": "to_start"},
        },
        row_width=1,
    )


start_markup = util.quick_markup(
    {
        "🪑 Забронировать место": {"callback_data": "make_booking_choose_date"},
        "⚙️ Управлять моими бронированиями": {"callback_data": "manage_my_bookings"},
        "👀 Узнать кто идёт в офис": {
            "callback_data": "see_colleagues_bookings_choose_date"
        },
        "🚶‍➡️ Оформить гостя": {"callback_data": "make_guest_choose_date"},
    },
    row_width=1,
)

start_markup_admin = util.quick_markup(
    {
        "🪑 Забронировать место": {"callback_data": "make_booking_choose_date"},
        "⚙️ Управлять моими бронированиями": {"callback_data": "manage_my_bookings"},
        "👀 Узнать кто идёт в офис": {
            "callback_data": "see_colleagues_bookings_choose_date"
        },
        "🚶‍➡️ Оформить гостя": {"callback_data": "make_guest_choose_date"},
        "🧑‍💻 Панель администратора": {"callback_data": "admin_options"},
    },
    row_width=1,
)


to_start_markup = util.quick_markup(
    {"⏪ В начало": {"callback_data": "to_start"}}, row_width=1
)


def date_selection_markup(available_dates: list[dict]) -> InlineKeyboardMarkup:
    """Сформировать клавиатуру под список  дат для просмотра мест доступных для бронирования на дату"""
    buttons = {}
    for date in available_dates:
        date_name = date["formatted"]
        button = {"callback_data": f"seats_on: {date['timestamp']}"}
        buttons[date_name] = button

    keyboard = util.quick_markup(buttons, row_width=2)
    keyboard.row(InlineKeyboardButton("⬅️ В начало", callback_data="to_start"))

    return keyboard


def see_colleagues_bookings_choose_date_markup(
    available_dates: list[dict],
) -> InlineKeyboardMarkup:
    """Сформировать клавиатуру под список дат для просмотра броней коллег"""
    buttons = {}
    for date in available_dates:
        date_name = date["formatted"]
        button = {"callback_data": f"see_colleagues_on: {date['timestamp']}"}
        buttons[date_name] = button

    keyboard = util.quick_markup(buttons, row_width=2)
    keyboard.row(InlineKeyboardButton("⬅️ В начало", callback_data="to_start"))

    return keyboard


def no_seats_markup(book_date) -> InlineKeyboardMarkup:
    """Сформировать клавиатуру под ситуацию когда бронировавшееся место ужe занято"""
    return util.quick_markup(
        {
            "📆 Выбрать другую дату": {"callback_data": "make_booking_choose_date"},
            "🤷 Прийти в офис без места": {
                "callback_data": f"book_wo_seat: {book_date}"
            },
            "👀 Кто идёт в эту дату": {
                "callback_data": f"see_colleagues_on: {book_date}"
            },
            "⏪ В начало": {"callback_data": "to_start"},
        },
        row_width=1,
    )


def seat_is_occupied_markup(book_date) -> InlineKeyboardMarkup:
    """Сформировать клавиатуру под ситуацию когда бронироавшееся место уже занято"""
    return util.quick_markup(
        {
            "🪑 Выбрать другое место": {"callback_data": f"seats_on: {book_date}"},
            "🤷 Прийти в офис без места": {
                "callback_data": f"book_wo_seat: {book_date}"
            },
            "👀 Кто идёт в эту дату": {
                "callback_data": f"see_colleagues_on: {book_date}"
            },
            "⏪ В начало": {"callback_data": "to_start"},
        },
        row_width=1,
    )


def seat_selection_markup(
    available_seats: list[str], book_date: str
) -> InlineKeyboardMarkup:
    """
    Сформировать клавиатуру под список мест для бронирования на дату
    """
    buttons = {}
    for seat in available_seats:
        button = {"callback_data": f"book_date_seat: {book_date}|{seat}"}
        buttons[seat] = button

    keyboard = util.quick_markup(buttons, row_width=3)
    keyboard.row(InlineKeyboardButton("⬅️ В начало", callback_data="to_start"))

    return keyboard


succesfull_booking_markup = util.quick_markup(
    {
        "🪑 Создать еще": {"callback_data": "make_booking_choose_date"},
        "⚙️ Управлять моими бронированиями": {"callback_data": "manage_my_bookings"},
        "👀 Узнать кто идёт в офис": {
            "callback_data": "see_colleagues_bookings_choose_date"
        },
        "⏪ В начало": {"callback_data": "to_start"},
    },
    row_width=1,
)

succesfull_guest_booking_markup = util.quick_markup(
    {
        "🪑 Создать еще": {"callback_data": "make_guest_choose_date"},
        "⚙️ Управлять моими бронированиями": {"callback_data": "manage_my_bookings"},
        "👀 Узнать кто идёт в офис": {
            "callback_data": "see_colleagues_bookings_choose_date"
        },
        "⏪ В начало": {"callback_data": "to_start"},
    },
    row_width=1,
)


manage_my_bookings_markup = util.quick_markup(
    {
        "❌ Выбрать бронирование для удаления": {"callback_data": "delete_booking"},
        "⏪ В начало": {"callback_data": "to_start"},
    },
    row_width=1,
)


def delete_booking_by_id_markup(bookings_id_list=list[int]) -> InlineKeyboardMarkup:
    """Сформировать клавиатуру под список id активных бронирований"""
    buttons = {}
    for booking_id in bookings_id_list:
        button = {"callback_data": f"booking_id_delete: {booking_id}"}
        buttons[booking_id] = button

    keyboard = util.quick_markup(buttons, row_width=3)
    keyboard.row(InlineKeyboardButton("↩️ Назад", callback_data="manage_my_bookings"))

    return keyboard


see_colleagues_on_markup = util.quick_markup(
    {"↩️ Назад": {"callback_data": "see_colleagues_bookings_choose_date"}}, row_width=1
)


def guest_date_selection_markup(available_dates: list[dict]) -> InlineKeyboardMarkup:
    """Сформировать клавиатуру под список дат для гостевого бронирования"""
    buttons = {}
    for date in available_dates:
        date_name = date["formatted"]
        button = {"callback_data": f"guest_seats_on: {date['timestamp']}"}
        buttons[date_name] = button

    keyboard = util.quick_markup(buttons, row_width=2)
    keyboard.row(InlineKeyboardButton("⬅️ В начало", callback_data="to_start"))

    return keyboard


def no_guest_seats_markup(book_date) -> InlineKeyboardMarkup:
    """
    Сформировать клавиатуру под ситуацию когда бронировавшееся место для гостя уже занято
    """
    return util.quick_markup(
        {
            "📆 Выбрать другую дату": {"callback_data": "make_guest_choose_date"},
            "🤷 Пригласить в офис без места": {
                "callback_data": f"guest_date_seat: {book_date}|no_seat"
            },
            "👀 Кто идёт в эту дату": {
                "callback_data": f"see_colleagues_on: {book_date}"
            },
            "⏪ В начало": {"callback_data": "to_start"},
        },
        row_width=1,
    )


def guest_seat_selection_markup(
    available_seats: list[str], book_date: str
) -> InlineKeyboardMarkup:
    """
    Сформировать клавиатуру под список мест для гостевого бронирования на дату
    """
    buttons = {}
    for seat in available_seats:
        button = {"callback_data": f"guest_date_seat: {book_date}|{seat}"}
        buttons[seat] = button

    keyboard = util.quick_markup(buttons, row_width=3)
    keyboard.row(InlineKeyboardButton("⬅️ В начало", callback_data="to_start"))

    return keyboard


def enter_guest_full_name_markup(book_date, seat_number) -> InlineKeyboardMarkup:
    """
    Сформировать клавиатуру для запроса ввода ФИО гостя
    """
    return util.quick_markup(
        {
            "✍️ Ввести": {
                "callback_data": f"write_guest_name: {book_date}|{seat_number}"
            },
            "⏪ В начало": {"callback_data": "to_start"},
        },
        row_width=1,
    )


name_forcereply_markup = ForceReply(input_field_placeholder="Иванов Иван Иванович")

admin_options_markup = util.quick_markup(
    {
        "Отвязать ФИО сотрудника от tg_id": {"callback_data": "users_w_tg_id_page: 0"},
        "Удалить сотрудника": {"callback_data": "delete_user_page: 0"},
        "Добавить сотрудника": {"callback_data": "add_user"},
        "Удалить бронирование": {"callback_data": "see_all_bookings"},
        "⏪ В начало": {"callback_data": "to_start"},
    },
    row_width=1,
)


def name_w_tg_id_selection_markup(
    users_w_tg_id: list[User], page: int = 0, total_pages: int = 0
) -> InlineKeyboardMarkup:
    """
    Создать на основе списка пользователей, информации о текущей странице
    и всего страницах клавиатуру с ФИО пользователей c user_id для отвязки tg_id
    """

    # Создаем кнопки с ФИО
    buttons = {}
    for user in users_w_tg_id:
        button = {"callback_data": f"untie_warn: {user.id}"}
        buttons[user.full_name] = button

    # Создаем кнопки навигации по страницам
    pagination_buttons = {}

    if total_pages > 1:
        if page > 0:
            pagination_buttons["◀️ Назад"] = {
                "callback_data": f"users_w_tg_id_page: {page - 1}"
            }

        if page < total_pages - 1:
            pagination_buttons["Вперед ▶️"] = {
                "callback_data": f"users_w_tg_id_page: {page + 1}"
            }

    pagination_buttons["⏪ В начало"] = {"callback_data": "to_start"}

    all_buttons = {**buttons, **pagination_buttons}

    return util.quick_markup(all_buttons, row_width=2)


def untie_warn_markup(user_id) -> InlineKeyboardMarkup:
    """
    Создать клавиатуру для подтверждения отвязки tg_id от ФИО
    """
    return util.quick_markup(
        {
            "Отвязать tg_id": {"callback_data": f"untie_make: {user_id}"},
            "⏪ В начало": {"callback_data": "to_start"},
        },
        row_width=1,
    )


def fullnames_selection_markup(
    all_fullnames: list[User], page: int = 0, total_pages: int = 0
) -> InlineKeyboardMarkup:
    """
    Создать на основе списка пользователей, информации о текущей странице
    и всего страницах клавиатуру с ФИО пользователей c user_id для удаления ФИО
    """

    # Создаем кнопки с ФИО
    buttons = {}
    for user in all_fullnames:
        button = {"callback_data": f"delete_warn: {user.id}"}
        buttons[user.full_name] = button

    # Создаем кнопки навигации по страницам
    pagination_buttons = {}

    if total_pages > 1:
        if page > 0:
            pagination_buttons["◀️ Назад"] = {
                "callback_data": f"delete_user_page: {page - 1}"
            }

        if page < total_pages - 1:
            pagination_buttons["Вперед ▶️"] = {
                "callback_data": f"delete_user_page: {page + 1}"
            }

    pagination_buttons["⏪ В начало"] = {"callback_data": "to_start"}

    all_buttons = {**buttons, **pagination_buttons}

    return util.quick_markup(all_buttons, row_width=2)


def delete_warn_markup(user_id) -> InlineKeyboardMarkup:
    """
    Создать клавиатуру для подтверждения удаления ФИО
    """
    return util.quick_markup(
        {
            "Удалить сотрудника": {"callback_data": f"delete_make: {user_id}"},
            "⏪ В начало": {"callback_data": "to_start"},
        },
        row_width=1,
    )
