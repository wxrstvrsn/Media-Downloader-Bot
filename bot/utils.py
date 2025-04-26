from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def normalize_youtube_url(url: str) -> str:
    """Приводит ссылку к нормальному виду."""
    url = url.strip()
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    if "shorts/" in url:
        video_id = url.split("shorts/")[1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    if "m.youtube.com" in url:
        url = url.replace("m.youtube.com", "youtube.com")
    return url


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def build_formats_keyboard(formats):
    """
    Строит клавиатуру с доступными форматами для скачивания.
    """
    seen = set()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for fmt in formats:
        resolution = fmt.get("resolution")
        ext = fmt.get("ext")
        itag = fmt.get("format_id")  # тут надо брать format_id!

        if not resolution or not ext or not itag:
            continue

        key = f"{resolution}_{ext}"
        if key in seen:
            continue
        seen.add(key)

        button = InlineKeyboardButton(
            text=f"{resolution} .{ext}",
            callback_data=f"format|{itag}|{ext}"
        )
        keyboard.inline_keyboard.append([button])

    return keyboard
