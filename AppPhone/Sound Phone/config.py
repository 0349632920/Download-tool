import os
from dotenv import load_dotenv

load_dotenv()

# Cấu hình Telegram Bot
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', 'YOUR_BOT_TOKEN_HERE')
ALLOWED_USERS = os.getenv('ALLOWED_USERS', '').split(',')

# Cấu hình ADB
ADB_PATH = os.getenv('ADB_PATH', 'adb')  # Đường dẫn đến adb, mặc định là 'adb'