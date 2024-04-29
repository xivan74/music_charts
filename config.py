import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

SUPER_BOT_TOKEN = os.getenv("MUSIC_SUPER_BOT_KEY", "")

private_chat_id = os.getenv("PRIVATE_CHAT_ID", "")
group_chat_id = os.getenv("GROUP_CHAT_ID", "")
work_chat_id = os.getenv("WORK_CHAT_ID", "")
admin_login = os.getenv("ADMIN_LOGIN", "")

BASE_DIR = Path(__file__).resolve().parent

db_url = os.getenv("DB_URL", "")
db_url2 = os.getenv("DB_URL2", "")


DATE_FORMAT = "%d.%m.%Y"
