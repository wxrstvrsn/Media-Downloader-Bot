import os

PUBLIC_URL = os.getenv("PUBLIC_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DOMAIN = os.getenv("DOMAIN")
DOWNLOAD_DIR = "bot/downloads"
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_COMMAND = os.getenv("ADMIN_COMMAND")
MAX_FILE_SIZE = 5000 * 1024 * 1024  # 500 MB

YDL_OPTS = {
    'outtmpl': DOWNLOAD_DIR + '/%(title)s.%(ext)s',
    'format': 'bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
    'quiet': True,
    'no_warnings': True,
}
