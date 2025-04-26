def normalize_youtube_url(url: str) -> str:
    """Приводит ссылку к нормальному виду."""
    url = url.strip()
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    if "shorts/" in url:
        video_id = url.split("shorts/")[1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    if "m.youtube.com" in url:
        url = url.replace("m.youtube.com", "youtube.com")
    return url