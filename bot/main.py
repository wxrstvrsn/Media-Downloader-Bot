import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from aiohttp import web

from config import BOT_TOKEN, ADMIN_ID, ADMIN_COMMAND, DOWNLOAD_DIR, PUBLIC_URL
from utils import normalize_youtube_url, build_formats_keyboard
from downloader import download_video, get_video_formats

# Словарь для хранения URL по юзеру
user_requests = {}

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

# Бот и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==== Хэндлер команды /start ====

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("👋 Отправьте ссылку на YouTube-видео для скачивания!")

# ==== Хэндлер команды для админа ====

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
        keyboard.append([InlineKeyboardButton(text=f"❌ {file}", callback_data=f"delete:{file}")])

    kb = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("🛠️ Файлы на сервере:", reply_markup=kb)

# ==== Хэндлер удаления файла админом ====

@dp.callback_query(F.data.startswith("delete:"))
async def delete_file(call: CallbackQuery):
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

# ==== Прием ссылки от пользователя ====

@dp.message()
async def catch_url(message: Message):
    url = message.text.strip()
    url = normalize_youtube_url(url)

    await message.answer("🔎 Ищу доступные форматы...")
    formats = get_video_formats(url)

    if not formats:
        await message.answer("❌ Не удалось получить форматы видео.")
        return

    # Сохраняем URL для пользователя
    user_requests[message.from_user.id] = url

    keyboard = build_formats_keyboard(formats)
    await message.answer("🔻 Выберите качество и формат:", reply_markup=keyboard)

# ==== Выбор формата ====

@dp.callback_query(F.data.startswith("format|"))
async def format_chosen(callback: CallbackQuery):
    await callback.answer()

    parts = callback.data.split("|")
    if len(parts) != 3:
        await callback.message.answer("❌ Неверные данные кнопки.")
        return

    _, itag, ext = parts

    # Получаем URL для этого пользователя
    url = user_requests.get(callback.from_user.id)
    if not url:
        await callback.message.answer("❌ Истекло время выбора. Пожалуйста, отправьте ссылку заново.")
        return

    msg = await callback.message.answer("⏳ Загружаю видео...")

    filename = await download_video(url, itag, ext)
    if filename:
        file_url = f"{PUBLIC_URL}/downloads/{filename}"
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="📥 Скачать файл", url=file_url)
        ]])
        await msg.edit_text(f"✅ Файл готов!\n{file_url}", reply_markup=kb)
    else:
        await msg.edit_text("❌ Ошибка при загрузке файла.")

# ==== AIOHTTP для отдачи файлов ====

async def downloads_handler(request):
    filename = request.match_info['filename']
    path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.isfile(path):
        return web.Response(status=404, text="File not found")
    return web.FileResponse(path)

async def start_web_app():
    app = web.Application()
    app.router.add_get('/downloads/{filename}', downloads_handler)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 8080))  # Railway даёт PORT в env
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"✅ HTTP сервер запущен на порту {port}")

# ==== MAIN ====

async def main():
    await start_web_app()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
