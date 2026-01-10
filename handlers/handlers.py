import datetime

from telebot.types import CallbackQuery, Message

import keyboards
import messages
import utils
from bot import bot, logger
from config.settings import settings
from scripts.preload_images import preloaded_images
from services import BookingService, UserService
from services.errors import *

from . import decorators


@decorators.error_command_handler
@bot.message_handler(commands=["start"])
async def start_command_handler(message: Message) -> None:
    """Обработчик команды /start"""
    try:
        user = await UserService.get_user_by_tg_id(tg_id=message.from_user.id)
        if user:
            # Если пользователь существует, то берется его имя (при неудаче - полное ФИО)
            name = (
                user.full_name.split()[1]
                if len(user.full_name.split()) > 1
                else user.full_name
            )
            await bot.send_message(
                message.chat.id,
                text=messages.start_message_w_name.format(name=name),
                # Проверяется никнейм пользователя на вхождение в список никнеймов админов
                # Отдается соответствующий набор кнопок
                reply_markup=(
                    keyboards.start_markup_admin
                    if message.from_user.username in settings.ADMIN_USERNAMES_LIST
                    else keyboards.start_markup
                ),
            )
            await bot.delete_message(message.chat.id, message.message_id, timeout=1)
        else:
            # Если пользователь не существует - предлагаем выбрать ФИО из незанятых
            free_users = await UserService.get_users_wo_tg_id(page=0)

            if not free_users:
                # Если свободных имен нет
                await bot.send_message(
                    message.chat.id,
                    text=messages.error_no_free_names_text,
                    reply_markup=keyboards.to_start_markup,
                )
                await bot.delete_message(message.chat.id, message.message_id, timeout=1)
                return

            # Создаем клавиатуру со свободными именами для первой страницы
            selection_keyboard = keyboards.name_selection_markup(
                free_users["users"], free_users["page"], free_users["total_pages"]
            )

            await bot.send_message(
                message.chat.id,
                text=messages.new_user_name_selection_text,
                reply_markup=selection_keyboard,
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
@bot.callback_query_handler(lambda query: query.data == "to_start")
async def handle_to_start_query(query: CallbackQuery) -> None:
    """Обработчик коллбека возврата в начало (to_start)"""
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        user = await UserService.get_user_by_tg_id(tg_id=query.from_user.id)
        if user:
            name = (
                user.full_name.split()[1]
                if len(user.full_name.split()) > 1
                else user.full_name
            )
            await bot.send_message(
                query.message.chat.id,
                text=messages.start_message_w_name.format(name=name),
                reply_markup=(
                    keyboards.start_markup_admin
                    if query.from_user.username in settings.ADMIN_USERNAMES_LIST
                    else keyboards.start_markup
                ),
            )
            await bot.delete_message(
                query.message.chat.id, query.message.message_id, timeout=1
            )
        else:
            # Пользователь не найден - предлагаем выбрать ФИО из незанятых
            free_users = await UserService.get_users_wo_tg_id(page=0)
            if not free_users:
                # Если свободных имен нет
                await bot.send_message(
                    query.chat.id,
                    text=messages.error_no_free_names_text,
                    reply_markup=keyboards.to_start_markup,
                )
                await bot.delete_message(
                    query.message.chat.id, query.message.message_id, timeout=1
                )
                return

            # Создаем клавиатуру со свободными именами для первой страницы
            selection_keyboard = keyboards.name_selection_markup(
                free_users["users"], free_users["page"], free_users["total_pages"]
            )
            await bot.send_message(
                query.message.chat.id,
                text=messages.new_user_name_selection_text,
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
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("users_page:")
)
async def handle_users_page_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека получения ФИО свободных пользователей
    (с указанием  номера страницы)  (users_page: page)
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        # Получаем пользователей для запрошенной страницы
        required_page = int(
            query.data.split(":")[1].strip()
        )  # Получаем номер требуемой страницы из callback_data
        free_users = await UserService.get_users_wo_tg_id(page=required_page)
        if not free_users["users"]:
            await bot.send_message(
                query.message.chat.id,
                text=messages.error_no_free_names_text,
                reply_markup=keyboards.to_start_markup,
            )
            await bot.delete_message(
                query.message.chat.id, query.message.message_id, timeout=1
            )
            return

        # Создаем клавиатуру со свободными именами для запрошенной страницы
        selection_keyboard = keyboards.name_selection_markup(
            free_users=free_users["users"],
            page=required_page,
            total_pages=free_users["total_pages"],
        )
        await bot.edit_message_reply_markup(
            chat_id=query.message.chat.id,
            message_id=query.message.message_id,
            reply_markup=selection_keyboard,
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
@bot.callback_query_handler(lambda query: query.data and query.data.startswith("reg:"))
async def handle_register_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека регистрации пользователя
    с выбранным ФИО (reg: user_id)
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        # Проверяем точно ли пользовтаель не перепутал имя (т.е. это точно его ФИО)
        user_id = int(
            query.data.split(":")[1].strip()
        )  # Получаем id записи users из callback_data
        user_data = await UserService.get_user_by_user_id(user_id)
        full_name = user_data.full_name
        await bot.send_message(
            query.message.chat.id,
            text=messages.preregister_verification_text.format(full_name=full_name),
            reply_markup=keyboards.confirm_registration_markup(user_id),
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
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("cnfm_reg:")
)
async def handle_confirm_reg_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека подтверждения регистрации
    пользователя с выбранным ФИО (cnfm_reg: user_id)
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        # Регистрируем пользователя с выбранным именем
        user = await UserService.update_user(
            user_id=int(query.data.split(":")[1].strip()),
            username=query.from_user.username,
            tg_id=query.from_user.id,
            chat_id=query.message.chat.id,
        )
        name = (
            user.full_name.split()[1]
            if len(user.full_name.split()) > 1
            else user.full_name
        )
        await bot.send_message(
            query.message.chat.id,
            text=messages.start_message_w_name.format(name=name),
            reply_markup=(
                keyboards.start_markup_admin
                if query.message.from_user.username in settings.ADMIN_USERNAMES_LIST
                else keyboards.start_markup
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
@bot.callback_query_handler(lambda query: query.data == "make_booking_choose_date")
async def handle_choose_booking_date_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса дат доступных для
    персонального бронирования (make_booking_choose_date)
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        available_dates = await BookingService.get_dates_wo_user_bookings(
            query.from_user.id
        )
        if not available_dates:
            await bot.send_message(
                query.message.chat.id,
                text=messages.no_free_dates_text,
                reply_markup=keyboards.to_start_markup,
            )
            await bot.delete_message(
                query.message.chat.id, query.message.message_id, timeout=1
            )
        else:
            # Создаем клавиатуру со свободными датами
            selection_keyboard = keyboards.date_selection_markup(available_dates)
            await bot.send_message(
                query.message.chat.id,
                text=messages.choose_date_text,
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
        return


@decorators.error_query_handler
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("seats_on: ")
)
async def handle_seats_on_date_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса мест доступных
    на выбранную дату (seats_on: date)
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        book_date = query.data.split(":")[1].strip()
        # проверяем что переданная дата есть в списке дат доступных для бронирования для пользователя
        available_dates = await BookingService.get_available_dates(query.from_user.id)
        if book_date not in [date["timestamp"] for date in available_dates]:
            await bot.send_message(
                query.message.chat.id,
                text=messages.no_seats_text,
                reply_markup=keyboards.no_seats_markup(book_date=book_date),
            )
            await bot.delete_message(
                query.message.chat.id, query.message.message_id, timeout=1
            )
            return

        # Создаем клавиатуру со свободными местами
        file_id = preloaded_images.get("office_map")
        available_seats = await BookingService.get_available_seats(book_date=book_date)
        selection_keyboard = keyboards.seat_selection_markup(available_seats, book_date)
        await bot.send_photo(
            query.message.chat.id,
            file_id,
            caption=messages.choose_seat_text,
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
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("book_date_seat: ")
)
async def handle_book_date_seat_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека создания персональной брони на выбранную дату и место
    (book_date_seat: book_date|seat)
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        booking_params = query.data.split(":")[1].strip().split("|")
        book_date, seat_number = booking_params[0], booking_params[1]
        book_date_obj = datetime.datetime.strptime(book_date, "%Y-%m-%d").date()
        # Создаем бронирование
        user_data = await UserService.get_user_by_tg_id(tg_id=query.from_user.id)
        user_id, full_name = user_data.id, user_data.full_name
        booking = await BookingService.create_booking(
            booking_date=book_date_obj,
            user_id=user_id,
            seat_number=seat_number,
            booking_type="personal",
            guest_full_name=None,
        )
        logger.info(
            "%s создал бронирование: дата: %s, место: %s, тип: 'personal'",
            full_name,
            book_date,
            seat_number,
        )
        file_id = preloaded_images.get("office_map")
        booking_date = utils.format_booking_date(book_date_obj)
        await bot.send_photo(
            query.message.chat.id,
            file_id,
            caption=messages.succesfull_booking_text.format(
                booking_date=booking_date, seat=booking.seat_number, full_name=full_name
            ),
            reply_markup=keyboards.succesfull_booking_markup,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )

    except BookingConflictError:
        await bot.send_message(
            query.message.chat.id,
            text=messages.seat_is_occupied_text,
            reply_markup=keyboards.seat_is_occupied_markup(book_date),
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
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("book_wo_seat: ")
)
async def handle_book_wo_seat_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека создания персонального посещения
    без места на выбранную дату (book_wo_seat: book_date)
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        book_date = query.data.split(":")[1].strip()
        book_date_obj = datetime.datetime.strptime(book_date, "%Y-%m-%d").date()
        # Создаем посещение без места
        user_data = await UserService.get_user_by_tg_id(tg_id=query.from_user.id)
        user_id, full_name = user_data.id, user_data.full_name
        booking = await BookingService.create_booking(
            booking_date=book_date_obj,
            seat_number=None,
            user_id=user_id,
            booking_type="personal_candidate",
            guest_full_name=None,
        )
        logger.info(
            "%s создал бронирование: дата: %s, место: без места, тип: 'personal_candidate'",
            full_name,
            book_date,
        )
        file_id = preloaded_images.get("office_map")
        await bot.send_photo(
            query.message.chat.id,
            file_id,
            caption=messages.succesfull_booking_text.format(
                booking_date=booking.booking_date, seat="XX", full_name=full_name
            ),
            reply_markup=keyboards.succesfull_booking_markup,
        )
        await bot.delete_message(
            query.message.chat.id, query.message.message_id, timeout=1
        )

    except BookingConflictError:
        await bot.send_message(
            query.message.chat.id,
            text=messages.seat_is_occupied_text,
            reply_markup=keyboards.seat_is_occupied_markup(book_date),
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
@bot.callback_query_handler(lambda query: query.data == "manage_my_bookings")
async def handle_manage_my_bookings_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека просмотра всех
    бронирований пользователя (manage_my_bookings)
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        user = await UserService.get_user_by_tg_id(tg_id=query.from_user.id)
        user_id, full_name = user.id, user.full_name
        users_bookings = await BookingService.get_user_future_bookings(user_id)
        # Создаем текст с данными всех будущих бронирований пользователя
        if users_bookings:
            bookings_text = messages.user_bookings_text_header.format(
                full_name=full_name
            )
            for booking in users_bookings:
                booking_date = utils.format_booking_date(booking.booking_date)
                booking_type = utils.get_booking_type_name(booking.type)
                seat_number = booking.seat_number if booking.seat_number else "XX"
                bookings_text += messages.user_bookings_text_item.format(
                    booking_date=booking_date,
                    seat=seat_number,
                    booking_type=booking_type,
                )
        else:
            bookings_text = messages.user_no_bookings_text
        file_id = preloaded_images.get("office_map")
        await bot.send_photo(
            query.message.chat.id,
            file_id,
            caption=bookings_text,
            reply_markup=keyboards.manage_my_bookings_markup,
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
@bot.callback_query_handler(lambda query: query.data == "delete_booking")
async def handle_delete_booking_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса списка бронирований
    пользователя для удаления (delete_booking)
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        user = await UserService.get_user_by_tg_id(tg_id=query.from_user.id)
        user_id, full_name = user.id, user.full_name
        users_bookings = await BookingService.get_user_future_bookings(user_id)
        # Создаем текст с данными всех будущих бронирований пользователя
        if users_bookings:
            bookings_text = messages.user_bookings_text_header.format(
                full_name=full_name
            )
            for booking in users_bookings:
                book_date = utils.format_booking_date(booking.booking_date)
                seat_number = booking.seat_number if booking.seat_number else "XX"
                booking_type = utils.get_booking_type_name(booking.type)
                bookings_text += messages.user_bookings_text_item_to_delete.format(
                    id=booking.id,
                    book_date=book_date,
                    seat=seat_number,
                    booking_type=booking_type,
                )
            selection_keyboard = keyboards.delete_booking_by_id_markup(
                sorted([booking.id for booking in users_bookings])
            )
        else:
            bookings_text = messages.user_no_bookings_text
            selection_keyboard = keyboards.to_start_markup

        await bot.send_message(
            query.message.chat.id, text=bookings_text, reply_markup=selection_keyboard
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


# Обработчик коллбека "удалить бронирование (booking_id_delete: booking_id)"
@decorators.error_query_handler
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("booking_id_delete:")
)
async def handle_booking_id_delete_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека удаления бронирования по
    его id (booking_id_delete: booking_id)
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        user = await UserService.get_user_by_tg_id(tg_id=query.from_user.id)
        full_name = user.full_name
        booking_id_to_delete = int(query.data.split(":")[1].strip())
        # тут можно добавить проверка на админ или что бронь автора запроса
        booking = await BookingService.delete_booking(booking_id=booking_id_to_delete)
        logger.info(
            "%s удалил %s бронирование ID %s, дата: %s, место: %s, тип: %s",
            full_name,
            "своё" if booking.user_id == user.id else "ЧУЖОЕ",
            booking.id,
            booking.booking_date,
            booking.seat_number,
            booking.type,
        )
        await bot.send_message(
            query.message.chat.id,
            text=messages.succesfull_booking_delete_text,
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
@bot.callback_query_handler(
    lambda query: query.data == "see_colleagues_bookings_choose_date"
)
async def handle_see_colleagues_bookings_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса дат с хотя бы одним
    посетителем (see_colleagues_bookings_choose_date)
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        dates_with_visitors = await BookingService.get_dates_with_visitors()
        if not dates_with_visitors:
            await bot.send_message(
                query.message.chat.id,
                text=messages.no_visitors_at_all_text,
                reply_markup=keyboards.to_start_markup,
            )
            await bot.delete_message(
                query.message.chat.id, query.message.message_id, timeout=1
            )
        else:
            dates_with_visitors = utils.format_dates_list(dates_with_visitors)
            selection_keyboard = keyboards.see_colleagues_bookings_choose_date_markup(
                dates_with_visitors
            )
            await bot.send_message(
                query.message.chat.id,
                text=messages.see_colleagues_bookings_choose_date_text,
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
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("see_colleagues_on: ")
)
async def handle_see_colleagues_on_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека просмотра бронирований коллег
    на выбранную дату (see_colleagues_on: date)
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        book_date = query.data.split(":")[1].strip()
        book_date_obj = datetime.datetime.strptime(book_date, "%Y-%m-%d").date()
        # получаем посетителей на дату
        visitors = await BookingService.get_visitors_by_date(date=book_date_obj)
        # Создаем текст с данными всех будущих бронирований коллег
        if visitors:
            bookings_text = messages.see_colleagues_bookings_on_date_text_header.format(
                book_date=utils.format_booking_date(book_date_obj)
            )
            for visitor in visitors:
                seat_number = visitor["seat_number"] if visitor["seat_number"] else "XX"
                booking_type = utils.get_booking_type_name(visitor["type"])
                bookings_text += (
                    messages.see_colleagues_bookings_on_date_text_item.format(
                        full_name=visitor["full_name"],
                        seat_number=seat_number,
                        booking_type=booking_type,
                    )
                )
        else:
            bookings_text = messages.no_visitors_text

        file_id = preloaded_images.get("office_map")
        await bot.send_photo(
            query.message.chat.id,
            file_id,
            caption=bookings_text,
            reply_markup=keyboards.see_colleagues_on_markup,
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
@bot.callback_query_handler(lambda query: query.data == "make_guest_choose_date")
async def handle_make_guest_choose_date_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса дат доступных
    для гостевого бронирования (make_guest_choose_date)
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)

        available_dates = await utils.generate_upcoming_dates()
        selection_keyboard = keyboards.guest_date_selection_markup(available_dates)
        await bot.send_message(
            query.message.chat.id,
            text=messages.choose_date_text,
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
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("guest_seats_on: ")
)
async def handle_guest_seats_on_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса мест доступных для гостевого
    бронирования на выбранную дату (guest_seats_on: date)
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        book_date = query.data.split(":")[1].strip()
        # проверяем что переданная дата есть в списке дат доступных для бронирования для гостевого бронирования
        available_dates = await BookingService.get_guest_available_dates()
        if book_date not in [date["timestamp"] for date in available_dates]:
            await bot.send_message(
                query.message.chat.id,
                text=messages.no_guest_seats_text,
                reply_markup=keyboards.no_guest_seats_markup(book_date=book_date),
            )
            await bot.delete_message(
                query.message.chat.id, query.message.message_id, timeout=1
            )
            return

        # Создаем клавиатуру со свободными местами
        file_id = preloaded_images.get("office_map")
        available_seats = await BookingService.get_available_seats(book_date=book_date)
        selection_keyboard = keyboards.guest_seat_selection_markup(
            available_seats, book_date
        )
        await bot.send_photo(
            query.message.chat.id,
            file_id,
            caption=messages.choose_seat_text,
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
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("guest_date_seat: ")
)
async def handle_guest_date_seat_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса интерфейса ручного ввода
    ФИО гостя (нажатие номера места)
    ("guest_date_seat: book_date|seat")
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        booking_params = query.data.split(":")[1].strip().split("|")
        book_date, seat_number = booking_params[0], (
            booking_params[1] if booking_params[1] != "no_seat" else None
        )
        # Предлагаем ввести ФИО
        await bot.send_message(
            query.message.chat.id,
            text=messages.enter_full_name_text,
            reply_markup=keyboards.enter_guest_full_name_markup(
                book_date, seat_number if seat_number else "no_seat"
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
@bot.callback_query_handler(
    lambda query: query.data and query.data.startswith("write_guest_name: ")
)
async def handle_write_guest_name_query(query: CallbackQuery) -> None:
    """
    Обработчик коллбека запроса на ручной ввод (нажатие "Ввести")
    ФИО гостя, создает "техническое сообщение" в чате с номером места и датой
    ("guest_date_seat: book_date|seat")
    """
    try:
        await bot.answer_callback_query(callback_query_id=query.id)
        booking_params = query.data.split(":")[1].strip().split("|")
        book_date, seat_number = booking_params[0], (
            booking_params[1] if booking_params[1] != "no_seat" else None
        )

        # Предлагаем ввести ФИО
        await bot.send_message(
            query.message.chat.id,
            text=messages.name_forcereply_text.format(
                book_date=book_date,
                seat_number=seat_number if seat_number else "no_seat",
            ),
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
@bot.message_handler(
    func=lambda message: message.reply_to_message
    and message.reply_to_message.text.startswith("Введите ФИО гостя")
)
async def handle_guest_full_name_input(message: Message) -> None:
    """
    Обработчик сообщения с введенным ФИО гостя
    (отправляет в чат "сообщение с ФИО гостя",
    удаляет "техническое сообщение" с номером места и датой и "сообщение с ФИО гостя",
    сразу создает бронирование)
    """
    try:
        booking_params = message.reply_to_message.text.split("|")
        book_date, seat_number = booking_params[1].strip(), (
            booking_params[2].strip()
            if booking_params[2].strip() != "no_seat"
            else None
        )
        book_date_obj = datetime.datetime.strptime(book_date, "%Y-%m-%d").date()
        full_name = message.text.strip()
        if not utils.is_full_name(full_name):
            await bot.delete_message(message.chat.id, message.message_id)
            if message.reply_to_message:
                try:
                    await bot.delete_message(
                        message.chat.id, message.reply_to_message.message_id
                    )
                except Exception as e:
                    await bot.send_message(
                        message.chat.id,
                        text=messages.error_text,
                        reply_markup=keyboards.to_start_markup,
                    )
                    await bot.delete_message(
                        message.chat.id, message.message_id, timeout=1
                    )
            await bot.send_message(
                message.chat.id,
                text=messages.error_invalid_full_name_text,
                reply_markup=keyboards.to_start_markup,
            )
            return

        # Создаем бронирование
        user_data = await UserService.get_user_by_tg_id(tg_id=message.from_user.id)
        booking = await BookingService.create_booking(
            booking_date=book_date_obj,
            user_id=user_data.id,
            seat_number=seat_number,
            booking_type="guest" if seat_number else "guest_candidate",
            guest_full_name=full_name,
        )
        logger.info(
            "%s создал бронирование: дата: %s, место: %s, тип: %s",
            full_name,
            book_date,
            seat_number if seat_number else "без места",
            "guest" if seat_number else "guest_candidate",
        )
        file_id = preloaded_images.get("office_map")
        seat_number = booking.seat_number if booking.seat_number else "XX"
        await bot.send_photo(
            message.chat.id,
            file_id,
            caption=messages.succesfull_booking_text.format(
                booking_date=booking.booking_date,
                seat=seat_number,
                full_name=booking.guest_full_name,
            ),
            reply_markup=keyboards.succesfull_booking_markup,
        )
        await bot.delete_message(message.chat.id, message.message_id, timeout=1)
        if message.reply_to_message:
            try:
                await bot.delete_message(
                    message.chat.id, message.reply_to_message.message_id
                )
            except Exception as e:
                await bot.send_message(
                    message.chat.id,
                    text=messages.error_text,
                    reply_markup=keyboards.to_start_markup,
                )
                await bot.delete_message(message.chat.id, message.message_id, timeout=1)

    except BookingConflictError:
        await bot.send_message(
            message.chat.id,
            text=messages.seat_is_occupied_text,
            reply_markup=keyboards.seat_is_occupied_markup(book_date),
        )
        await bot.delete_message(message.chat.id, message.message_id, timeout=1)
        return

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


# # Обработчик неопознанного коллбека
# @error_handlers.error_query_handler
# @bot.callback_query_handler(func=lambda query: True)
# async def handle_unknown_query(query: CallbackQuery):
#     print("Неопознанный колбэк: ", query.data, flush=True)
