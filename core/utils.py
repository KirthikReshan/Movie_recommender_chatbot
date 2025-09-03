# core/utils.py
import logging
from pathlib import Path
import json

LOG_PATH = Path(__file__).resolve().parents[1] / "logs"
LOG_PATH.mkdir(exist_ok=True)
LOG_FILE = LOG_PATH / "chatbot.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def log_info(msg: str):
    logging.info(msg)

def md_movie_line(movie: dict) -> str:
    """
    Returns a markdown line for a movie dict (from TMDb).
    Example: - [Title (2020) — 8.1★](https://www.themoviedb.org/movie/ID)
    """
    title = movie.get("title") or movie.get("name") or "Untitled"
    year = (movie.get("release_date") or "")[:4]
    rating = movie.get("vote_average")
    movie_id = movie.get("id")
    url = f"https://www.themoviedb.org/movie/{movie_id}" if movie_id else ""
    rating_str = f"{rating:.1f}★" if (isinstance(rating, (int, float))) else "N/A"
    if year:
        return f"- [{title} ({year}) — {rating_str}]({url})"
    return f"- [{title} — {rating_str}]({url})"

def load_genres_map(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # normalize keys
        return {k.lower(): v for k, v in data.items()}
    except Exception:
        return {}
