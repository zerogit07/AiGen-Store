import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN tidak ditemukan di file .env")

ADMIN_ID = os.getenv("ADMIN_ID")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID tidak ditemukan di file .env")
ADMIN_ID = int(ADMIN_ID)

# Path database (relatif terhadap file config.py)
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "shop.db")