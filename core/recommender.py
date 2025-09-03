# core/recommender.py
import requests
from urllib.parse import urljoin
from config.settings import TMDB_API_KEY, BASE_URL
from .utils import log_info

TIMEOUT = 10

def _get(path: str, params: dict = None, use_key_param=True):
    url = urljoin(BASE_URL + "/", path.lstrip("/"))
    params = params or {}
    if use_key_param:
        params = {**params, "api_key": TMDB_API_KEY}
    resp = requests.get(url, params=params, timeout=TIMEOUT)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        log_info(f"HTTP error for {url} -> {resp.status_code} {resp.text}")
        raise
    return resp.json()

def discover_movies(params: dict, limit: int = 10):
    """
    Uses /discover/movie to get movies matching params. Pages if needed.
    """
    results = []
    page = 1
    while len(results) < limit and page <= 5:
        p = {**params, "page": page}
        data = _get("/discover/movie", p)
        results.extend(data.get("results", []))
        if page >= data.get("total_pages", 0):
            break
        page += 1
    return results[:limit]

def search_movies(query: str, limit: int = 10):
    params = {"query": query, "page": 1, "include_adult": False}
    data = _get("/search/movie", params)
    return data.get("results", [])[:limit]

def get_movie_details(movie_id: int):
    return _get(f"/movie/{movie_id}", {"append_to_response": "videos,credits"})
