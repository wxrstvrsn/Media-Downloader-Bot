import logging
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types
from aiogram.filters import Command
from aiohttp import web
from dotenv import load_dotenv
from downloader import get_video_formats, download_video
from config import *
from utils import *

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

file_callback = CallbackData("file", "filename")
format_callback = CallbackData("format", "itag")

user_data = {}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("👋 Отправь мне ссылку на YouTube видео, и я помогу тебе скачать его!")

@dp.message(Command(ADMIN_COMMAND))
async def admin_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У тебя нет доступа к этой команде.")
        return

    files = os.listdir(DOWNLOAD_DIR)
    if not files:
        await message.answer("📂 Папка загрузок пуста.")
        return

    kb = InlineKeyboardMarkup(row_width=1)
    for file in files:
        short_name = file if len(file) <= 40 else file[:37] + "..."
        kb.add(
            InlineKeyboardButton(
                text=short_name,
                callback_data=file_callback.new(filename=file)
            )
        )

    await message.answer("🛠️ Доступные файлы на сервере:", reply_markup=kb)
@dp.callback_query(F.data.startswith("delete:"))
async def delete_file(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("🚫 Нет доступа.", show_alert=True)
        return

    filename = call.data.split("delete:")[1]
    path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
        await call.answer(f"✅ Удалено {filename}")
        await call.message.delete()
    else:
        await call.answer("⚠️ Файл не найден.")

@dp.message()
async def catch_url(message: types.Message):
    url = normalize_youtube_url(message.text)

    if not url.startswith("http"):
        await message.answer("❌ Это не ссылка.")
        return

    await message.answer("🔎 Ищу доступные форматы...")

    formats = get_video_formats(url)
    if not formats:
        await message.answer("❌ Не удалось получить форматы.")
        return

    seen = set()
    keyboard = []

    for fmt in formats:
        key = f"{fmt['resolution']}_{fmt['ext']}"
        if key not in seen:
            seen.add(key)
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{fmt['resolution']} .{fmt['ext']}",
                    callback_data=f"{fmt['format_id']}"
                )
            ])

    kb = InlineKeyboardMarkup(inline_keyboard=keyboard)
    user_data[message.chat.id] = url
    await message.answer("🔻 Выбери качество:", reply_markup=kb)

@dp.callback_query()
async def process_choice(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    format_id = call.data
    url = user_data.get(chat_id)

    if not url:
        await call.answer("❗ Истекло время ссылки.")
        return

    progress_message = await bot.send_message(chat_id=chat_id, text="⏳ Загружаю файл...")

    filename = download_video(url, format_id, DOWNLOAD_DIR)

    if not filename:
        await progress_message.edit_text("❌ Ошибка загрузки файла.")
        return

    public_url = f"{PUBLIC_URL}/downloads/{os.path.basename(filename)}"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать файл", url=public_url)]
    ])

    await progress_message.edit_text(f"✅ Файл готов!\n{public_url}", reply_markup=keyboard)

async def start_web_app():
    app = web.Application()
    app.router.add_static('/downloads', DOWNLOAD_DIR, show_index=False)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    logger.info("HTTP сервер запущен на порту 8000.")

async def main():
    await start_web_app()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
