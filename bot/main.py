import os
import logging
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiohttp import web

from downloader import get_video_formats, download_video
from config import BOT_TOKEN, DOWNLOAD_DIR, PUBLIC_URL, PORT, ADMIN_ID
from utils import *

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Бот
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Веб-сервер для файлов
async def start_web_app():
    app = web.Application()
    app.router.add_static('/downloads', DOWNLOAD_DIR, show_index=False)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 Web server started at {PUBLIC_URL}/downloads")

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("👋 Отправь ссылку на видео!")

# Обработчик команды /admin
@dp.message(Command("admin"))
async def admin_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("🚫 Доступ запрещён.")
        return

    files = os.listdir(DOWNLOAD_DIR)
    if not files:
        await message.answer("📂 Папка downloads пуста.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for filename in files:
        button = InlineKeyboardButton(
            text=f"📄 {filename}",
            url=f"{PUBLIC_URL}/downloads/{filename}"
        )
        kb.inline_keyboard.append([button])

    await message.answer("🛠️ Файлы на сервере:", reply_markup=kb)


# Обработчик обычного текста (ссылок)
@dp.message()
async def catch_url(message: Message):
    url = normalize_youtube_url(message.text.strip())
    if not url:
        await message.answer("❌ Неверная ссылка. Отправьте корректную ссылку на YouTube-видео.")
        return

    await message.answer("🔎 Ищу доступные форматы...")
    formats = get_video_formats(url)
    if not formats:
        await message.answer("❌ Не удалось получить форматы видео.")
        return

    # Убираем дубликаты форматов
    seen = set()
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for fmt in formats:
        resolution = fmt["resolution"]
        ext = fmt["ext"]
        itag = fmt["itag"]

        key = (resolution, ext)
        if key in seen:
            continue
        seen.add(key)

        button = InlineKeyboardButton(
            text=f"{resolution} .{ext}",
            callback_data=f"format|{itag}|{url}"
        )
        kb.inline_keyboard.append([button])

    await message.answer("🔻 Выберите качество:", reply_markup=kb)

# Обработчик выбора формата
@dp.callback_query(F.data.startswith("format|"))
async def format_chosen(callback: CallbackQuery):
    await callback.answer()
    _, itag, url = callback.data.split("|", 2)

    msg = await callback.message.answer("⏳ Загружаю видео...")

    filename = await download_video(url, itag)
    if filename:
        file_url = f"{PUBLIC_URL}/downloads/{filename}"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📥 Скачать видео", url=file_url)]
        ])

        await msg.edit_text("✅ Файл загружен!", reply_markup=keyboard)
    else:
        await msg.edit_text("❌ Ошибка при загрузке файла.")

# Запуск
async def main():
    await start_web_app()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


