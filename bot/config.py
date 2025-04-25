import os
from dotenv import load_dotenv

load_dotenv()

# Токен Telegram бота
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Хост для aiohttp (слушаем все интерфейсы)
BIND_HOST = '0.0.0.0'
PORT = 8000

# Публичный адрес, по которому можно скачать файл (меняй на IP или домен при надобности)
PUBLIC_URL = os.getenv('PUBLIC_URL', f'http://localhost:{PORT}')

# Папка загрузок
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# URL для формирования ссылок
DOWNLOAD_BASE_URL = f'{PUBLIC_URL}/downloads'

# Опции yt-dlp
YDL_OPTS = {
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'format': 'bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
    'quiet': True,
    'no_warnings': True,
}


# Максимальный размер файла
MAX_FILE_SIZE = 5000 * 1024 * 1024  # 50 MB
