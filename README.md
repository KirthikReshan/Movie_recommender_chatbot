# Movie Recommender Chatbot

Run:
1. Copy `.env.example` -> `.env` and add your TMDB_API_KEY.
2. Install deps:
   pip install -r requirements.txt
3. Start Streamlit:
   streamlit run app.py

Usage:
- Ask things like "Top 10 Tamil movies", "Best sci-fi 2010s", or "search Inception".
- The app auto-detects language, genre, rating band, decade, and uses TMDb discover/search.

Notes:
- Keep your .env secret.
- Logs saved in logs/chatbot.log
