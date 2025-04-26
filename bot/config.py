import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_COMMAND = os.getenv("ADMIN_COMMAND", "admin")

PUBLIC_URL = os.getenv("PUBLIC_URL")
DOWNLOAD_DIR = "bot/downloads"
BIND_HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 8000))
