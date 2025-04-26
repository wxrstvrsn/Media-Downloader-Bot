import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiohttp import web
from downloader import get_video_formats, download_video

# Конфиг
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "bot/downloads")
PUBLIC_URL = os.getenv("PUBLIC_URL")
BIND_HOST = os.getenv("BIND_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Бот
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Web-сервер для раздачи файлов
async def start_web_app():
    app = web.Application()
    app.router.add_static('/downloads', DOWNLOAD_DIR, show_index=False)  # ЗАПРЕТИТЬ листинг файлов
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, BIND_HOST, PORT)
    await site.start()
    logger.info(f"Web server started at {PUBLIC_URL}/downloads")

# Состояние выбора формата
user_requests = {}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("👋 Отправьте ссылку на видео!")

@dp.message(Command("REMOVED"))
async def admin_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещён.")
        return

    files = os.listdir(DOWNLOAD_DIR)
    if not files:
        await message.answer("📂 Папка downloads пуста.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for filename in files:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🗑️ {filename}",
                callback_data=f"delete:{filename}"
            )
        ])

    await message.answer("🧾 Список файлов в downloads:", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("delete:"))
async def delete_file_callback(callback_query: CallbackQuery):
    filename = callback_query.data.split("delete:")[1]
    file_path = os.path.join(DOWNLOAD_DIR, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        await callback_query.message.answer(f"✅ Файл {filename} удалён.")
    else:
        await callback_query.message.answer(f"⚠️ Файл {filename} не найден.")
    await callback_query.answer()

@dp.message()
async def catch_url(message: types.Message):
    url = message.text.strip()

    await message.answer("🔎 Ищу доступные форматы...")
    formats = get_video_formats(url)
    if not formats:
        await message.answer("❌ Не удалось получить форматы видео.")
        return

    seen = set()
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for fmt in formats:
        resolution = fmt["resolution"]
        ext = fmt["ext"]
        key = f"{resolution}_{ext}"
        if key in seen:
            continue
        seen.add(key)
        button = InlineKeyboardButton(
            text=f"{resolution} .{ext}",
            callback_data=f"{resolution}:{ext}"
        )
        kb.inline_keyboard.append([button])

    await message.answer("🔻 Выбери качество и формат:", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("format:"))
async def process_choice(call: CallbackQuery):
    await call.answer()

    parts = call.data.split(":")
    url = parts[1]
    format_id = parts[2]

    chat_id = call.message.chat.id

    await bot.send_message(chat_id, "⏬ Загружаю ваш файл...")

    filepath, filename = download_video(url, format_id, DOWNLOAD_DIR)
    if filepath:
        file_url = f"{PUBLIC_URL}/downloads/{filename}"
        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="⬇️ Скачать файл", url=file_url)
        )
        await bot.send_message(chat_id=chat_id, text=f"✅ Ваш файл готов!\nНазвание: {filename}", reply_markup=kb)
    else:
        await bot.send_message(chat_id, "❌ Ошибка при загрузке файла.")

async def main():
    await start_web_app()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
