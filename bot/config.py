import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
PUBLIC_URL = os.getenv("PUBLIC_URL")  # Если хочешь оставить ссылки на скачку
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

YDL_OPTS = {
    'outtmpl': DOWNLOAD_DIR + '/%(title)s.%(ext)s',
    'format': 'bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
    'quiet': True,
    'no_warnings': True,
}
