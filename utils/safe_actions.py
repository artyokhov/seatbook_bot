from enum import Enum
from typing import Optional, Union

from telebot.types import CallbackQuery, InlineKeyboardMarkup, Message

import messages
from bot import bot
from scripts.preload_images import preloaded_images


class MessageContentType(str, Enum):
    TEXT = "text"
    MEDIA = "media"


async def safely_delete_message(chat_id: int, message_id: int) -> None:
    """
    "Безопасно" удаляет сообщение: пытается удалить с таймаутом секунда,
    если не удалось - меняет текст сообщения и удаляет кнопки. Если не получилось,
    то пытается сделать тоже самое с подписью под фото. Если не получилось, то ничего не делает.
    Функция существует для обхода ограничения Телеграм на удаление сообщений страше 48 часов.
    """
    try:
        await bot.delete_message(chat_id, message_id, timeout=1)
    except Exception:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=messages.outdated_message_text,
                reply_markup=None,
            )
        except:
            try:
                await bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=message_id,
                    caption=messages.outdated_message_text,
                    reply_markup=None,
                )
            except Exception:
                pass


async def safely_replace_message(
    source: Union[Message, CallbackQuery],
    *,
    new_message_type: MessageContentType,
    new_text: Optional[str],
    new_reply_markup: Optional[InlineKeyboardMarkup] = None,
    new_photo_file_id: Optional[str] = None,
) -> None:
    """
    Заменяет текст сообщения или само сообщение: определяет "желаемый тип нового сообщения"
    и "тип обрабатываемого сообщения" и в зависимости от контекста применяет то или
    иное действие к сообщению.
    """

    # Унификация входных данных
    if isinstance(source, CallbackQuery):
        message = source.message
        chat_id = source.message.chat.id
    else:
        message = source
        chat_id = source.chat.id

    message_id = message.message_id
    current_type = message.content_type
    # в зависимости от типа контента обрабатываемого сообщения
    # и типа контента ожидаемого сообщения выбирается действие
    try:
        # в текущем решении всегда меняется текст
        if new_text is None:
            raise TypeError(f"new_text must be str, got {type(new_text)}")
        # для отлдаки: всегда ожидается строка
        if new_text is not None and not isinstance(new_text, str):
            raise TypeError(f"new_text must be str, got {type(new_text)}")
        # когда нужно заменить только текст
        if new_text and not new_photo_file_id:
            # при замене текста на текст
            if new_message_type == MessageContentType.TEXT and current_type == "text":
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=new_text,
                        reply_markup=new_reply_markup,
                    )

                    return
                except:
                    # если не получилось поменять текст текстового сообщения,
                    # то пытаемся удалить и отправляем новое
                    await bot.send_message(
                        chat_id=chat_id,
                        text=new_text,
                        reply_markup=new_reply_markup,
                    )
                    await safely_delete_message(chat_id, message_id)

                    return
            # при замене подписи под фото на подпись под фото
            if new_message_type == MessageContentType.MEDIA and current_type in {
                "photo",
                "video",
                "document",
            }:
                try:
                    await bot.edit_message_caption(
                        chat_id=chat_id,
                        message_id=message_id,
                        caption=new_text,
                        reply_markup=new_reply_markup,
                    )
                    return
                except:
                    file_id = (
                        new_photo_file_id
                        if new_photo_file_id
                        else preloaded_images.get("office_map")
                    )
                    # если не получилось поменять подпись под фото,
                    # то пытаемся удалить и отправляем новое фото
                    await bot.send_photo(
                        chat_id,
                        file_id,
                        caption=new_text,
                        reply_markup=new_reply_markup,
                    )
                    await safely_delete_message(chat_id, message_id)
                    return

            # если новое сообщение это текстовое сообщение,
            # а методом исключения текущее это "сообщение с фото",
            # то исправить сообщение нельзя, можно только удалить и отправить новое
            if new_message_type == MessageContentType.TEXT:
                await bot.send_message(
                    chat_id=chat_id,
                    text=new_text,
                    reply_markup=new_reply_markup,
                )
                await safely_delete_message(chat_id, message_id)

                return

            # если новое сообщение это "сообщение с фото",
            # а методом исключения текущее это текстовое сообщение,
            # то исправить сообщение нельзя, можно только удалить и отправить новое
            if new_message_type == MessageContentType.MEDIA:
                file_id = (
                    new_photo_file_id
                    if new_photo_file_id
                    else preloaded_images.get("office_map")
                )
                await bot.send_photo(
                    chat_id,
                    file_id,
                    caption=new_text,
                    reply_markup=new_reply_markup,
                )
                await safely_delete_message(chat_id, message_id)

                return
        # все прочие сценарии текущая версия сервиса не поддерживает
        # TO DO: реализовать в будущем логику с new_photo_file_id и вызов edit_message_media(),
        # сейчас это не нужно т.к. нет сценария корректировки изображения в сообщении
        # TO DO: реализовать в будущем логику с edit_message_reply_markup()
        else:
            return

    except Exception:

        raise Exception
