import os

# Базовый URL вашего сервиса, например "https://<app>.up.railway.app"
PUBLIC_URL = os.getenv("PUBLIC_URL")

BOT_TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN")

# Папка для хранения скачанных файлов — на одном уровне с кодом
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")

ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_COMMAND = os.getenv("ADMIN_COMMAND")

BIND_HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 8080))  # для aiohttp

MAX_FILE_SIZE = 480 * 1024 * 1024  # 480 MB

# Опции для yt_dlp
YDL_OPTS = {
    # Файлы будут сохраняться в DOWNLOAD_DIR/<title>.<ext>
    'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
    'format': 'bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
    'quiet': True,
    'no_warnings': True,
}
