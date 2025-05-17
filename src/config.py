# src/config.py
import os
from dotenv import load_dotenv

# Определяем путь к .env файлу относительно текущего файла (config.py)
# config.py находится в src/, .env - на уровень выше (в корне проекта)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Это будет корень проекта
DOTENV_PATH = os.path.join(BASE_DIR, '.env')

# Загружаем переменные из .env файла
if os.path.exists(DOTENV_PATH):
    load_dotenv(dotenv_path=DOTENV_PATH)
else:
    print(f"Warning: .env file not found at {DOTENV_PATH}. Using default values or expecting system env vars.")

# Версия клиентского PyQt приложения из .env
CLIENT_APP_VERSION = os.environ.get("CLIENT_APP_VERSION_ENV", "1.0.0") # Значение по умолчанию, если в .env нет
BACKEND_BASE_URL = os.environ.get("CRYPTO_BACKEND_URL", "http://127.0.0.1:8000")

print(BACKEND_BASE_URL)
print(f"Client App Version loaded from config: {CLIENT_APP_VERSION}") # Для отладки

def configure_logging():
    pass