# core/parser.py
import re
from pathlib import Path
from .utils import load_genres_map

BASE_DIR = Path(__file__).resolve().parents[1]
GENRES_PATH = BASE_DIR / "data" / "genres.json"
GENRE_MAP = load_genres_map(GENRES_PATH)

LANG_MAP = {
    "tamil":"ta","hindi":"hi","telugu":"te","malayalam":"ml","kannada":"kn",
    "english":"en","japanese":"ja","korean":"ko","chinese":"zh","mandarin":"zh",
    "french":"fr","spanish":"es","german":"de","italian":"it"
}

COUNTRY_MAP = {
    "india":"IN","india":"IN","usa":"US","america":"US","us":"US","uk":"GB",
    "japan":"JP","korea":"KR","south korea":"KR","china":"CN","france":"FR",
    "spain":"ES","germany":"DE","italy":"IT"
}

def _detect_genre(q: str):
    for name in GENRE_MAP.keys():
        if name in q:
            return GENRE_MAP[name]
    return None

def _detect_language(q: str):
    for k, v in LANG_MAP.items():
        if k in q:
            return v
    return None

def _detect_country(q: str):
    for k, v in COUNTRY_MAP.items():
        if k in q:
            return v
    return None

def _detect_rating_band(q: str):
    ql = q.lower()
    if any(w in ql for w in ["best","top","high","very good","excellent"]):
        return {"vote_average.gte": 8.0}
    if any(w in ql for w in ["mid","middle","decent","good"]):
        return {"vote_average.gte": 6.5, "vote_average.lte": 8.0}
    if "low" in ql or "bad" in ql:
        return {"vote_average.lte": 6.0}
    return {}

def _detect_years(q: str):
    # explicit year
    m = re.search(r"(19|20)\d{2}", q)
    if m:
        return {"primary_release_year": int(m.group())}
    # decades: 90s, 2000s, 2010s
    if "90s" in q or "1990s" in q:
        return {"primary_release_date.gte":"1990-01-01","primary_release_date.lte":"1999-12-31"}
    if "80s" in q or "1980s" in q:
        return {"primary_release_date.gte":"1980-01-01","primary_release_date.lte":"1989-12-31"}
    if "2000s" in q or "2000s" in q:
        return {"primary_release_date.gte":"2000-01-01","primary_release_date.lte":"2009-12-31"}
    if "2010s" in q or "2010s" in q:
        return {"primary_release_date.gte":"2010-01-01","primary_release_date.lte":"2019-12-31"}
    return {}

def parse_query(q: str):
    """
    Returns a tuple: (mode, params, limit, search_term)
    mode: "discover" (use discover endpoint) or "search" (search by name)
    params: dict for discover or search params
    limit: int max results to return
    search_term: raw search string (only for search mode)
    """
    ql = q.lower()
    params = {
        "language": "en-US",
        "sort_by": "vote_average.desc",
        "vote_count.gte": 50  # reasonable threshold
    }

    # limit / top N
    n = re.search(r"\btop\s*(\d{1,2})\b", ql)
    if n:
        limit = max(1, min(30, int(n.group(1))))
    else:
        # try "give me 5" or "show 7"
        m = re.search(r"\b(\d{1,2})\b", ql)
        limit = int(m.group(1)) if m else 10

    # rating band
    params.update(_detect_rating_band(ql))

    # genre
    genre_id = _detect_genre(ql)
    if genre_id:
        params["with_genres"] = genre_id

    # language
    lang = _detect_language(ql)
    if lang:
        params["with_original_language"] = lang

    # country
    country = _detect_country(ql)
    if country:
        params["with_origin_country"] = country

    # year/decade
    params.update(_detect_years(ql))

    # Decide mode:
    # If user explicitly says "search", or asks by title words (e.g., "find 'inception'") -> search
    if any(token in ql for token in ["search", "find", "play", "watch", "movie called", "movie:"]):
        mode = "search"
        search_term = re.sub(r".*(search|find|play|watch|movie called|movie:)\s*", "", ql).strip()
        search_term = search_term.strip('"\' ')
        return mode, params, limit, (search_term or q.strip())
    # Heuristics: if user included genre, rating band, decade -> use discover
    if genre_id or "top" in ql or any(k in ql for k in ["best","high","mid","201","199","90s","2010s"]):
        return "discover", params, limit, None

    # Default: search by query
    return "search", params, limit, q.strip()
