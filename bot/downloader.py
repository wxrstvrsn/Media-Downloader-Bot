import os
import logging
from yt_dlp import YoutubeDL
from config import YDL_OPTS, MAX_FILE_SIZE, DOWNLOAD_DIR

logger = logging.getLogger(__name__)
COOKIES_PATH = "cookies.txt"


def build_opts(extra_opts=None):
    opts = {
        'quiet': True,
        'no_warnings': True,
    }
    if os.path.exists(COOKIES_PATH):
        opts['cookiefile'] = COOKIES_PATH
    if extra_opts:
        opts.update(extra_opts)
    return opts


def get_video_formats(url: str):
    try:
        opts = build_opts()
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        available_formats = []
        for fmt in formats:
            # выбираем только форматы с видео-дорожкой
            if fmt.get('height') and fmt.get('ext') and fmt.get('vcodec') != 'none':
                available_formats.append({
                    'format_id': fmt['format_id'],
                    'resolution': f"{fmt['height']}p",
                    'ext': fmt['ext']
                })
        return sorted(available_formats,
                      key=lambda x: int(x['resolution'][:-1]),
                      reverse=True)
    except Exception as e:
        logger.error(f"Ошибка при получении форматов: {e}")
        return []


def safe_filename(ext: str) -> str:
    # Считаем, сколько уже файлов в папке
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    total = len([
        f for f in os.listdir(DOWNLOAD_DIR)
        if os.path.isfile(os.path.join(DOWNLOAD_DIR, f))
    ])
    return f"filename_{total + 1}{ext}"


def download_video(url: str, format_id: str):
    try:
        logger.info(f"Start downloading: {url}, format: {format_id}+bestaudio")

        # Узнаём инфо без скачивания
        with YoutubeDL(build_opts()) as ydl:
            ydl.extract_info(url, download=False)

        # Готовим опции для загрузки
        download_opts = YDL_OPTS.copy()
        download_opts['format'] = f"{format_id}+bestaudio"
        if os.path.exists(COOKIES_PATH):
            download_opts['cookiefile'] = COOKIES_PATH

        # Скачиваем
        with YoutubeDL(download_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)

        # Проверяем размер
        size = os.path.getsize(filepath)
        if size > MAX_FILE_SIZE:
            os.remove(filepath)
            raise ValueError(f"Файл слишком большой: {size/1024**2:.1f} MB")

        # Переименовываем в безопасное имя
        ext = os.path.splitext(filepath)[1]
        new_name = safe_filename(ext)
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        final_path = os.path.join(DOWNLOAD_DIR, new_name)
        os.rename(filepath, final_path)

        logger.info(f"Downloaded: {final_path} ({size/1024**2:.1f} MB)")
        # возвращаем только имя файла, без пути
        return new_name

    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        return None
