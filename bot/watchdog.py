import os
import time
import subprocess
import requests
from dotenv import set_key, load_dotenv, dotenv_values

NGROK_PATH = "ngrok"
ENV_PATH = ".env"
PORT = 8000
CHECK_INTERVAL = 60  # секунд

ngrok_process = None
bot_process = None


def start_ngrok():
    global ngrok_process
    print("[watchdog] Запуск ngrok...")
    ngrok_process = subprocess.Popen([NGROK_PATH, "http", str(PORT)], stdout=subprocess.DEVNULL)
    time.sleep(3)

    try:
        response = requests.get("http://localhost:4040/api/tunnels")
        tunnels = response.json()["tunnels"]
        public_url = tunnels[0]["public_url"]
        print(f"[watchdog] Новый публичный URL: {public_url}")

        # Обновляем .env
        set_key(ENV_PATH, "PUBLIC_URL", public_url)
        return public_url
    except Exception as e:
        print(f"[watchdog] Не удалось получить ссылку от ngrok: {e}")
        return None


def start_bot(public_url):
    global bot_process
    print("[watchdog] Запуск бота...")

    env = os.environ.copy()
    env["PUBLIC_URL"] = public_url

    # передаём в бот текущие переменные, если они есть
    env.update(dotenv_values(ENV_PATH))

    bot_process = subprocess.Popen(["python", "main.py"], env=env)


def stop_all():
    global ngrok_process, bot_process
    clear_old_env_state()
    if ngrok_process:
        ngrok_process.terminate()
        ngrok_process.wait()
    if bot_process:
        bot_process.terminate()
        bot_process.wait()
    print("[watchdog] Остановлены все процессы.")


def check_tunnel_alive(public_url):
    try:
        response = requests.get(public_url + "/downloads", timeout=10)
        return response.status_code == 200
    except:
        return False


def clear_old_env_state():
    """
    Удаляет LAST_USER_URL, LAST_USER_FORMAT, LAST_CHAT_ID из .env
    """
    print("[watchdog] Очистка старого состояния из .env...")
    if not os.path.exists(ENV_PATH):
        return

    lines = []
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.startswith(("LAST_USER_URL", "LAST_USER_FORMAT", "LAST_CHAT_ID")):
                lines.append(line)

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    load_dotenv(ENV_PATH)
    clear_old_env_state()

    public_url = start_ngrok()
    if public_url:
        start_bot(public_url)

    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            if not check_tunnel_alive(public_url):
                print("[watchdog] Туннель не отвечает. Перезапускаю всё...")
                stop_all()
                public_url = start_ngrok()
                if public_url:
                    start_bot(public_url)
    except KeyboardInterrupt:
        print("[watchdog] Остановка по Ctrl+C...")
        stop_all()


if __name__ == "__main__":
    main()
