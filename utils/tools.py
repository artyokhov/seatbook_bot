import re


def is_full_name(s: str) -> bool:
    """
    Проверяет, что строка состоит из трёх слов через пробел,
    каждое слово начинается с большой буквы, остальные — маленькие.
    """
    # Убираем лишние пробелы по краям и между словами
    s = " ".join(s.strip().split())

    # Проверка через regex: 3 слова, каждое с заглавной буквы и маленькими далее
    pattern = r"^[А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+$"
    return bool(re.match(pattern, s))


def get_booking_type_name(booking_type: str) -> str:
    """Преобразует внутреннее имя типа бронирования в человекочитаемое."""
    type_mapping = {
        "personal": "Сотрудник",
        "guest": "Гость",
        "personal_candidate": "Сотрудник (без места)",
        "guest_candidate": "Гость (без места)",
    }
    return type_mapping.get(booking_type, "Неизвестный тип")


def split_bookings_html_by_b_tags(
    text: str, bookings_ids: list[int], max_len: int = 4096
) -> list[dict]:
    """
    Делит HTML-текст на чанки, не разрывая <b>...</b> блоки.
    Каждый чанк имеет список номеров бронирований для селектора.
    """
    if len(text) < 4096:
        return [{"text_part": text, "bookings_ids": bookings_ids}]
    else:
        parts = []
        current = ""
        first_position = 0
        last_position = 0

        # Разбиваем по закрывающему тегу
        blocks = text.split("</b>")

        for block in blocks:

            last_position += 1
            if block.strip():
                block = block + "</b>"  # возвращаем закрывающий тег

            if len(current) + len(block) <= max_len:
                current += block
            else:
                parts.append(
                    {
                        "text_part": current,
                        "bookings_ids": bookings_ids[
                            first_position : last_position - 1
                        ],
                    }
                )
                first_position = last_position - 1
                current = block

        if current:
            parts.append(
                {"text_part": current, "bookings_ids": bookings_ids[first_position:]}
            )

        return parts
