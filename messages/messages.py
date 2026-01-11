import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

from telebot import formatting

start_message_w_name = formatting.format_text(
    "👋 Привет, ",
    formatting.hbold("{name}"),
    "!\n\n",
    "Что хочешь сделать?",
    separator="",
)

error_no_free_names_text = "🚷 К сожалению, свободных записей ФИО сотрудника нет. Обратитесь к администратору для внесения ФИО в конфиг приложения. 🚷"

new_user_name_selection_text = formatting.format_text(
    "🆔 Вы ещё не зарегистрированы.\n\n",
    "Пожалуйста, выберите своё ФИО из списка ниже.\n",
    formatting.hbold("Внимание: "),
    formatting.hitalic(
        "В БД будут записаны ваши telegram id и telegram никнейм и связаны с вашим ФИО"
    ),
    separator="",
)

preregister_verification_text = formatting.format_text(
    "🧐 Проверьте данные:\n\n",
    formatting.hbold("{full_name}"),
    "\n\n",
    "Это ваше ФИО?",
    separator="",
)

choose_date_text = "📅 Выберите дату для бронирования рабочего места"

no_free_dates_text = (
    "📆 На ближайшие 2 недели у вас уже есть все возможные бронирования."
)

no_seats_text = formatting.format_text(
    "😕 На эту дату свободных мест больше нет.\n\n",
    "Вы можете выбрать другую дату или прийти в офис без места.",
    separator="",
)

seat_is_occupied_text = formatting.format_text(
    "⛔ Это место только что заняли.\n\n",
    "Выберите другое место или приходите без бронирования.",
    separator="",
)

choose_seat_text = "Выберите место"

succesfull_booking_text = formatting.format_text(
    "✅ Бронирование подтверждено!\n\n",
    "📅 Дата: ",
    formatting.hbold("{booking_date}"),
    "\n🪑 Место: ",
    formatting.hbold("{seat}"),
    "\n\n",
    "👤 На имя: ",
    formatting.hbold("{full_name}"),
    separator="",
)

user_no_bookings_text = "У вас пока нет активных бронирований. 💭"

user_bookings_text_header = formatting.format_text(
    "📌 Ваши активные бронирования:\n\n", separator=""
)

user_bookings_text_item = formatting.format_text(
    "📅 ",
    formatting.hbold("{booking_date}"),
    "\n🪑 ",
    "{seat}",
    " — ",
    "{booking_type}",
    "\n\n",
    separator="",
)

user_bookings_text_item_to_delete = formatting.format_text(
    "👉 ",
    formatting.hunderline("ID брони:"),
    formatting.hbold(" {id}"),
    " 👈\n",
    "{book_date}",
    " - место: ",
    formatting.hbold("{seat}\n"),
    "Тип брони: ",
    "{booking_type}",
    "\n\n",
    separator="",
)

error_text = (
    "🔴 Произошла ошибка.\n\n" "Пожалуйста, попробуйте ещё раз или вернитесь в начало."
)

error_w_caption_text = formatting.format_text(formatting.hbold("{error_caption}"))


def prepare_error_caption(e: Exception) -> str:
    """Генерирует краткое описание ошибки из исключения."""
    tb = traceback.extract_tb(e.__traceback__)
    last_frame = tb[-1] if tb else None
    location = (
        f"{last_frame.filename}:{last_frame.lineno} ({last_frame.name})"
        if last_frame
        else "unknown location"
    )
    timestamp = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S")

    return (
        f"⛔ Ошибка\n\n"
        f"🕒 {timestamp}\n"
        f"📌 {type(e).__name__}\n"
        f"💬 {str(e)}\n"
        f"📍 {location}"
    )


succesfull_booking_delete_text = "Бронирование было успешно удалено 🤟"

see_colleagues_bookings_choose_date_text = (
    "В офисе будут люди в эти даты. Выберите дату для просмотра."
)

see_colleagues_bookings_on_date_text_header = formatting.format_text(
    "В выбранную дату (<b>{book_date}</b>) планируют прийти\n\n", separator=""
)

see_colleagues_bookings_on_date_text_item = formatting.format_text(
    "🙆 ",
    formatting.hbold("{full_name}"),
    ", \n",
    "{seat_number}",
    " - ",
    "{booking_type}",
    "\n\n",
    separator="",
)

no_visitors_text = "На эту дату нет посетителей. 💭"

no_visitors_at_all_text = "Никто не собирается в офис в ближайшие 2 недели. 💭"

enter_full_name_text = formatting.format_text(
    "Введите ФИО гостя. \n",
    formatting.hbold("Три слова через пробел c большой буквы. \n\n"),
    "Пример: ",
    formatting.hbold("Иванов Иван Иванович"),
    "\n",
    separator="",
)

name_forcereply_text = formatting.format_text(
    "Введите ФИО гостя\n\n", " | ", "{book_date}", " | ", "{seat_number}", separator=""
)

error_invalid_full_name_text = (
    "Введенное ФИО не отвечает требованиям:\n\nТри слова через пробел c большой буквы"
)

no_guest_seats_text = formatting.format_text(
    "💭 Свободных мест на эту дату уже нет.\n\n",
    formatting.hbold("Выберите другую дату"),
    " или пригласите гостя в офис ",
    formatting.hbold("без забронированного места"),
    ".",
    separator="",
)


admin_options_text = "🧑‍💻 Панель администратора\n\nВыберите действие:"


users_w_tg_id_page_selection_text = (
    "Выберите сотрудника которого нужно отвязать от tg_id"
)

untie_warn_text = formatting.format_text(
    "⚠️ Внимание!\n\n",
    "После этого действия у ",
    formatting.hbold("{full_name}:\n\n"),
    "• будут удалены все бронирования\n",
    "• ФИО станет доступно для новой регистрации",
    separator="",
)

untie_success_text = (
    "Сотрудник успешно отвязан от tg_id и все его бронирования удалены."
)

delete_page_selection_text = "Выберите сотрудника которого нужно удалить из системы"

delete_warn_text = formatting.format_text(
    "После этого действия у ",
    formatting.hbold("{full_name}:  \n"),
    "1) Все бронирования пользователя (и персональные и гостевые)",
    formatting.hbold("будут удалены;\n"),
    formatting.hbold("2) ФИО пользователя будет удалено из БД ->"),
    "оно станет недоступным для регистрации нового пользователя",
)

delete_success_text = "Сотрудник успешно удален и все его бронирования удалены."

new_user_name_forcereply_text = formatting.format_text(
    "Введите ФИО нового сотрудника. \n",
    formatting.hbold("Три слова через пробел c большой буквы. \n\n"),
    "Пример: ",
    formatting.hbold("Иванов Иван Иванович"),
    "\n",
    separator="",
)

new_user_success_text = formatting.format_text(
    "Пользователь ", formatting.hbold("{full_name}"), "добавлен в систему"
)


future_bookings_list_header = formatting.format_text(
    "Активные бронирования:\n\n", separator=""
)

future_bookings_list_item = formatting.format_text(
    formatting.hbold(
        "ID: {booking_id} - {booking_date} - {seat} - {booking_type} - {full_name}\n"
    ),
    separator="",
)

no_future_booking_text = "Никто не планирует посещать офис в ближайшие 14 дней. 💭"

outdated_message_text = formatting.format_text(
    formatting.hitalic("⏳ Это сообщение устарело. Актуальное ниже 👇"), separator=""
)
