import os

PUBLIC_URL = os.getenv("PUBLIC_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN")
DOWNLOAD_DIR = "bot/downloads"
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_COMMAND = os.getenv("ADMIN_COMMAND")
BIND_HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 8000))
MAX_FILE_SIZE = 480 * 1024 * 1024  # 480 MB

YDL_OPTS = {
    'outtmpl': DOWNLOAD_DIR + '/%(title)s.%(ext)s',
    'format': 'bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
    'quiet': True,
    'no_warnings': True,
}
