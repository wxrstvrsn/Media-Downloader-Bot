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

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# CallbackData
file_callback = CallbackData("file", filename=str)
format_callback = CallbackData("format", itag=str)

# Сервер для скачивания файлов
async def start_web_app():
    app = web.Application()
    app.router.add_static('/downloads', DOWNLOAD_DIR, show_index=False)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, BIND_HOST, PORT)
    await site.start()
    logger.info(f"Web server started at {PUBLIC_URL}/downloads")

# Команда старт
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("🖖 В дорогу собрался? 🫔Вкуснях купил? Молодца "
                         "🥤Некуда втыкать зенки, вворачивая очередной джанкфуд?"
                         "💾Кидай ссылочку на ютуб, щ сделаем!")

# Админка для файлов
@dp.message(Command("admin"))
async def admin_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещён.")
        return

    files = os.listdir(DOWNLOAD_DIR)
    if not files:
        await message.answer("📂 Папка пуста.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📄 {f}", callback_data=file_callback.new(filename=f))]
        for f in files
    ])

    await message.answer("🛠️ Файлы на сервере:", reply_markup=kb)
# Обработка выбора файла
@dp.callback_query(file_callback.filter())
async def send_file(call: types.CallbackQuery, callback_data: dict):
    filename = callback_data['filename']
    file_path = os.path.join(DOWNLOAD_DIR, filename)

    if not os.path.exists(file_path):
        await call.message.answer("❌ Файл не найден.")
        return

    await call.message.answer_document(types.FSInputFile(file_path))
# Поймать ссылку на видео
@dp.message(F.text)
async def catch_url(message: types.Message):
    url = normalize_youtube_url(message.text)
    if not url:
        await message.answer("❗ Пожалуйста, отправьте корректную ссылку на видео.")
        return

    await message.answer("🔎 Ищу доступные форматы...")
    formats = get_video_formats(url)
    if not formats:
        await message.answer("❌ Не удалось получить форматы.")
        return

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
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{resolution} {ext}",
                callback_data=format_callback.new(itag=str(itag))
            )
        ])

    await message.answer("🔻 Выберите формат:", reply_markup=kb)

# Выбор формата
@dp.callback_query(format_callback.filter())
async def download_selected(call: types.CallbackQuery, callback_data: dict):
    itag = callback_data["itag"]
    url = call.message.reply_to_message.text if call.message.reply_to_message else None

    if not url:
        await call.message.answer("❌ Не удалось получить ссылку.")
        return

    normalized_url = normalize_youtube_url(url)
    if not normalized_url:
        await call.message.answer("❗ Некорректная ссылка.")
        return

    loading_message = await call.message.answer("⏳ Загружаю ваш файл...")

    try:
        filename = await download_video(normalized_url, itag)
    except Exception as e:
        logger.error(f"Ошибка при загрузке видео: {e}")
        await loading_message.edit_text("❌ Ошибка при загрузке видео.")
        return

    await loading_message.edit_text(f"✅ Ваш файл загружен: {PUBLIC_URL}/downloads/{filename}")


# Запуск
async def main():
    await start_web_app()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())