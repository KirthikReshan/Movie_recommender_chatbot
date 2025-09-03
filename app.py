# app.py
import streamlit as st
from pathlib import Path
import requests
import re
from core.parser import parse_query
from core.recommender import discover_movies, search_movies
from core.utils import log_info, load_genres_map

BASE_IMG_URL = "https://image.tmdb.org/t/p/w200"
OMDB_API_KEY = "your_omdb_api_key"

# --- Page setup ---
st.set_page_config(page_title="🎬 Movie Recommender Pro", layout="wide")
st.title("🎬 Movie Recommender — Pro Mode")

# --- Sidebar filters ---
st.sidebar.header("Filters")
genres_file = Path(__file__).parent / "data" / "genres.json"
genres_map = load_genres_map(genres_file)
selected_genre = st.sidebar.selectbox("Genre", ["Any"] + list(genres_map.keys()))
selected_lang = st.sidebar.text_input("Language (e.g., Tamil, English)", "")
year_range = st.sidebar.slider("Year range", 1950, 2025, (2000, 2025))
min_tmdb_rating = st.sidebar.slider("Minimum TMDb Rating", 0.0, 10.0, 6.0)
min_imdb_rating = st.sidebar.slider("Minimum IMDb Rating", 0.0, 10.0, 0.0)

# --- Search input ---
user_input = st.text_input(
    "🔍 Search or ask for recommendations",
    placeholder="Try: 'Top 10 movies', 'best sci-fi 2010s', 'search inception', 'Tamil 2025 movies'",
    key="main_search"
)

# --- Session state ---
if "movies" not in st.session_state or st.session_state.get("last_query") != user_input:
    st.session_state.movies = []
    st.session_state.page = 0
    st.session_state.last_query = user_input

# --- Cached API calls ---
@st.cache_data(show_spinner=False)
def get_movies(mode, params=None, limit=20, term=None):
    if mode == "discover":
        return discover_movies(params, limit=limit)
    else:
        return search_movies(term, limit=limit)

@st.cache_data(show_spinner=False)
def get_imdb_info(imdb_id):
    if not imdb_id:
        return None
    url = f"http://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_API_KEY}"
    try:
        res = requests.get(url, timeout=5).json()
        if res.get("Response") == "True" and res.get("imdbRating") != "N/A":
            return {"rating": float(res.get("imdbRating")), "url": f"https://www.imdb.com/title/{imdb_id}/"}
    except requests.RequestException:
        return None
    return None

# --- Map languages to TMDb codes ---
LANGUAGE_MAP = {
    "tamil": "ta",
    "english": "en",
    "hindi": "hi",
    "korean": "ko",
    "japanese": "ja",
    "french": "fr"
}

# --- Extract year & language from search query ---
def extract_year_and_lang(query):
    query_lower = query.lower()
    year_match = re.search(r"\b(19|20)\d{2}\b", query_lower)
    year = int(year_match.group()) if year_match else None

    lang = None
    for name, code in LANGUAGE_MAP.items():
        if name in query_lower:
            lang = code
            break
    return year, lang

# --- Process input ---
if user_input.strip():
    try:
        mode, params, limit, search_term = parse_query(user_input.strip())
        log_info(f"Query: {user_input} => mode={mode}, params={params}, limit={limit}, search_term={search_term}")

        # Auto-detect year & language from query
        detected_year, detected_lang = extract_year_and_lang(user_input)
        if detected_year:
            params["primary_release_date.gte"] = f"{detected_year}-01-01"
            params["primary_release_date.lte"] = f"{detected_year}-12-31"
        else:
            params["primary_release_date.gte"] = f"{year_range[0]}-01-01"
            params["primary_release_date.lte"] = f"{year_range[1]}-12-31"

        if detected_lang:
            params["with_original_language"] = detected_lang
        elif selected_lang.lower() in LANGUAGE_MAP:
            params["with_original_language"] = LANGUAGE_MAP[selected_lang.lower()]

        if selected_genre != "Any":
            params["with_genres"] = genres_map[selected_genre]
        params["vote_average.gte"] = min_tmdb_rating

        movies = get_movies(mode, params=params, term=search_term, limit=50)
        st.session_state.movies = movies

    except Exception as e:
        log_info(f"Error processing query '{user_input}': {e}")
        st.session_state.movies = []
        st.error(f"⚠️ Error: {e}")

# --- Pagination setup ---
movies_per_page = 12
page = st.session_state.page
movies = st.session_state.movies
total_pages = (len(movies) - 1) // movies_per_page + 1
start_idx = page * movies_per_page
end_idx = start_idx + movies_per_page
display_movies = movies[start_idx:end_idx]

# --- Display movies ---
if display_movies:
    cols_per_row = 4
    for i in range(0, len(display_movies), cols_per_row):
        row_cols = st.columns(cols_per_row)
        for idx, movie in enumerate(display_movies[i:i + cols_per_row]):
            with row_cols[idx]:
                # Poster
                if movie.get("poster_path"):
                    st.image(BASE_IMG_URL + movie["poster_path"], use_container_width=True)

                # Title + Year
                title = movie.get("title", "Unknown")
                year = movie.get("release_date", "")[:4]
                st.markdown(f"**{title} ({year})**")

                # TMDb rating
                tmdb_rating = movie.get("vote_average", 'N/A')
                st.markdown(f"⭐ TMDb: {tmdb_rating}")

                # IMDb rating
                imdb_id = movie.get("imdb_id")
                imdb_info = get_imdb_info(imdb_id) if imdb_id else None
                if imdb_info and imdb_info['rating'] >= min_imdb_rating:
                    st.markdown(f"🎯 IMDb: {imdb_info['rating']}")
                    st.markdown(f"[View on IMDb]({imdb_info['url']})")

                # Genres
                genres = ", ".join([g for g, gid in genres_map.items() if gid in movie.get("genre_ids", [])])
                if genres:
                    st.markdown(f"🎬 Genre: {genres}")

                # Overview snippet
                overview = movie.get("overview", "")
                if overview:
                    st.markdown(f"📝 {overview[:120]}{'...' if len(overview) > 120 else ''}")

                # TMDb link
                if movie.get("id"):
                    tmdb_url = f"https://www.themoviedb.org/movie/{movie['id']}"
                    st.markdown(f"[View on TMDb]({tmdb_url})")

    # --- Pagination buttons ---
    col_prev, col_page, col_next = st.columns([1,1,1])
    with col_prev:
        if st.button("⬅ Previous") and page > 0:
            st.session_state.page -= 1
            st.rerun()
    with col_page:
        st.markdown(f"Page {page+1} of {total_pages}")
    with col_next:
        if st.button("Next ➡") and page < total_pages - 1:
            st.session_state.page += 1
            st.rerun()
else:
    if user_input.strip():
        st.info("No movies found. Try changing filters or search term.")

# --- Hints ---
st.markdown("---")
st.markdown(
    "**Hints:**\n- Use `top 10`, `best`, `mid` for rating filters.\n- Mention language/country like `Tamil`, `India`, `Korean`.\n- Include year like `2025`.\n- Use `search <movie name>` to look up a title."
)
