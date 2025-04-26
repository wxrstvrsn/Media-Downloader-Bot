# created by wxrstvrsn
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def normalize_youtube_url(url: str) -> str:
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

def build_formats_keyboard(formats):
    seen = set()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for fmt in formats:
        res = fmt.get("resolution")
        ext = fmt.get("ext")
        itag = fmt.get("format_id")
        if not res or not ext or not itag:
            continue
        key = f"{res}_{ext}"
        if key in seen:
            continue
        seen.add(key)
        btn = InlineKeyboardButton(
            text=f"{res} .{ext}",
            callback_data=f"format|{itag}|{ext}"
        )
        keyboard.inline_keyboard.append([btn])
    return keyboard
