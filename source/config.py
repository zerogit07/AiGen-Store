import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN tidak ditemukan di file .env")

ADMIN_ID = int(os.getenv("ADMIN_ID"))
DASHBOARD_USER = os.getenv("DASHBOARD_USER", "admin")
DASHBOARD_PASS = os.getenv("DASHBOARD_PASS", "admin123")
print(f"DEBUG: Loaded User={DASHBOARD_USER}, Pass={DASHBOARD_PASS}")

# Path database (relatif terhadap file config.py)
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "shop.db")