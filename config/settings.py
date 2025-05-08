import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / "config/.env")

STEAM_KEY = os.getenv("STEAM_API_KEY")
