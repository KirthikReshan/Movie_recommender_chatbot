# config/settings.py
from dotenv import load_dotenv
import os
from pathlib import Path

# load .env from project root
root = Path(__file__).resolve().parents[1]
load_dotenv(root / ".env")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_READ_ACCESS_TOKEN = os.getenv("TMDB_READ_ACCESS_TOKEN", "")
BASE_URL = "https://api.themoviedb.org/3"

if not TMDB_API_KEY:
    raise RuntimeError("TMDB_API_KEY not found. Put it in .env (see .env.example).")
