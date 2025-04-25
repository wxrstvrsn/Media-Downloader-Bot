import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
from downloader import get_video_formats, download_video
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
PUBLIC_URL = os.getenv("PUBLIC_URL")
LAST_USER_URL = os.getenv("LAST_USER_URL")
LAST_USER_FORMAT = os.getenv("LAST_USER_FORMAT")
LAST_CHAT_ID = os.getenv("LAST_CHAT_ID")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_links = {}


async def start_web_app():
    app = web.Application()
    app.router.add_static("/downloads", DOWNLOAD_DIR, show_index=True)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    logger.info(f"Web server started at {PUBLIC_URL}/downloads")


@dp.message(F.text.startswith("http"))
async def handle_url(message: types.Message):
    url = message.text.strip()
    user_links[message.from_user.id] = {
        "url": url,
        "chat_id": message.chat.id
    }
    await send_format_buttons(message.chat.id, url)


async def send_format_buttons(chat_id: int, url: str):
    formats = get_video_formats(url)
    if not formats:
        await bot.send_message(chat_id=chat_id, text="❌ Не удалось получить форматы видео.")
        return

    kb = InlineKeyboardBuilder()
    for fmt in formats:
        label = f"{fmt['resolution']} .{fmt['ext']}"
        kb.button(
            text=label,
            callback_data=f"dl|{fmt['format_id']}|{fmt['ext']}"
        )
    kb.adjust(2)
    await bot.send_message(chat_id=chat_id, text="Выберите качество и формат:", reply_markup=kb.as_markup())


@dp.callback_query(F.data.startswith("dl|"))
async def process_choice(call: types.CallbackQuery):
    _, format_id, ext = call.data.split("|")
    user_id = call.from_user.id
    user_data = user_links.get(user_id)

    if not user_data:
        await call.message.answer("❌ Не удалось определить ссылку.")
        return

    url = user_data["url"]
    chat_id = user_data["chat_id"]

    # сохраняем выбор
    os.environ["LAST_USER_URL"] = url
    os.environ["LAST_USER_FORMAT"] = format_id
    os.environ["LAST_CHAT_ID"] = str(chat_id)
    with open(".env", "a") as f:
        f.write(f"\nLAST_USER_URL={url}\nLAST_USER_FORMAT={format_id}\nLAST_CHAT_ID={chat_id}\n")

    filepath = download_video(url, format_id, ext)
    if not filepath:
        await bot.send_message(chat_id=chat_id, text="❌ Не удалось скачать видео.")
        return

    filename = os.path.basename(filepath)
    link = f"{PUBLIC_URL}/downloads/{filename}"
    kb = InlineKeyboardBuilder()
    kb.button(text="⬇️ Скачать видео", url=link)
    await bot.send_message(chat_id=chat_id, text=f"✅ Ваш файл готов!\nНазвание: {filename}", reply_markup=kb.as_markup())


async def try_resume_download():
    if LAST_USER_URL and LAST_USER_FORMAT and LAST_CHAT_ID:
        logger.info("[main.py] Восстановление после сбоя ngrok: повторная загрузка...")
        await send_format_buttons(int(LAST_CHAT_ID), LAST_USER_URL)


async def main():
    await start_web_app()
    await try_resume_download()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
