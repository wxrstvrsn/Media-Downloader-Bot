import os
import logging
import asyncio
import re

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.filters import Command
from aiohttp import web

from downloader import get_video_formats, download_video
from config import BOT_TOKEN, DOWNLOAD_DIR, PUBLIC_URL, PORT, ADMIN_ID, ADMIN_COMMAND
from utils import *
from urllib.parse import quote, unquote

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Бот
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_data = {}
async def set_default_commands(bot):
    await bot.set_my_commands([BotCommand(command="start", description="Пингануть")])

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("👋 Отправьте ссылку на видео с YouTube для скачивания!")


# Веб-сервер для файлов
async def start_web_app():
    app = web.Application()
    app.router.add_static('/downloads', DOWNLOAD_DIR, show_index=False)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 Web server started at {PUBLIC_URL}/downloads")


from urllib.parse import quote  # В начале файла добавь импорт!

@dp.message(Command(ADMIN_COMMAND))
async def admin_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("🚫 У вас нет прав для этой команды.")
        return

    files = os.listdir(DOWNLOAD_DIR)
    if not files:
        await message.answer("📂 Папка загрузок пуста.")
        return

    keyboard = []
    for file in files:
        safe_file = quote(file)  # Экранируем имя файла для передачи в callback_data
        keyboard.append([
            InlineKeyboardButton(text=f"❌ {file}", callback_data=f"delete|{safe_file}")
        ])

    kb = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("🛠️ Файлы на сервере:", reply_markup=kb)


@dp.callback_query(F.data.startswith("delete|"))
async def delete_file(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("🚫 Нет доступа.", show_alert=True)
        return

    encoded_filename = call.data.split("delete|")[1]
    filename = unquote(encoded_filename)  # Декодируем обратно оригинальное имя файла
    path = os.path.join(DOWNLOAD_DIR, filename)

    if os.path.exists(path):
        os.remove(path)
        await call.answer(f"✅ Удалено {filename}")
        await call.message.delete()
    else:
        await call.answer("⚠️ Файл не найден.")



# Обработчик обычного текста (ссылок)
@dp.message()
async def catch_url(message: Message):
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


# Обработчик выбора формата
@dp.callback_query()
async def process_choice(call: CallbackQuery):
    chat_id = call.message.chat.id
    format_id = call.data
    url = user_data.get(chat_id)

    if not url:
        await call.answer("❗ Истекло время ссылки.")
        return

    progress_message = await bot.send_message(chat_id=chat_id, text="⏳ Загружаю файл...")

    filename = download_video(url, format_id)

    if not filename:
        await progress_message.edit_text("❌ Ошибка загрузки файла.")
        return

    safe_filename = quote(os.path.basename(filename))  # <-- исправление: экранируем имя файла
    public_url = f"{PUBLIC_URL}/downloads/{safe_filename}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать файл", url=public_url)]
    ])

    await progress_message.edit_text(f"✅ Файл готов!\n{public_url}", reply_markup=keyboard)


# Запуск
async def main():
    await start_web_app()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
