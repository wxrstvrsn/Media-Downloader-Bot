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
    """
    Получает список доступных форматов видео (с расширением и разрешением).
    """
    try:
        opts = build_opts()
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        available_formats = []
        for fmt in formats:
            if fmt.get('height') and fmt.get('ext') and not fmt.get('vcodec') == 'none':
                available_formats.append({
                    'format_id': fmt['format_id'],
                    'resolution': f"{fmt['height']}p",
                    'ext': fmt['ext']
                })
        return sorted(available_formats, key=lambda x: int(x['resolution'][:-1]), reverse=True)
    except Exception as e:
        logger.error(f"Ошибка при получении форматов: {e}")
        return []

def safe_filename(ext: str) -> str:
    total_files = len([
        f for f in os.listdir(DOWNLOAD_DIR)
        if os.path.isfile(os.path.join(DOWNLOAD_DIR, f))
    ])
    return f"filename_{total_files + 1}{ext}"

def download_video(url: str, format_id: str):
    try:
        logger.info(f"Start downloading: {url}, format: {format_id}+bestaudio")

        pre_opts = build_opts()
        with YoutubeDL(pre_opts) as ydl:
            pre_info = ydl.extract_info(url, download=False)

        download_opts = YDL_OPTS.copy()
        download_opts['format'] = f"{format_id}+bestaudio"

        if os.path.exists(COOKIES_PATH):
            download_opts['cookiefile'] = COOKIES_PATH

        with YoutubeDL(download_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)

        final_size = os.path.getsize(filepath)
        if final_size > MAX_FILE_SIZE:
            os.remove(filepath)
            raise ValueError(f"Файл слишком большой: {final_size/1024**2:.1f} MB")

        tempExt = os.path.splitext(filepath)[1]
        new_name = safe_filename(tempExt)
        new_path = os.path.join(DOWNLOAD_DIR, new_name)

        os.rename(filepath, new_path)

        logger.info(f"Downloaded successfully: {new_path} ({final_size/1024**2:.1f} MB)")
        return new_path

    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        return None
