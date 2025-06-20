import sqlite3
from sqlite3 import Error

DATABASE_NAME = "hangman_cache.db"

def create_connection():
    """ create a database connection to the SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        print(f"Successfully connected to SQLite database: {DATABASE_NAME}")
        return conn
    except Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_tables(conn):
    """ create tables from the create_table_sql statements """
    sql_create_english_words_table = """
    CREATE TABLE IF NOT EXISTS english_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT UNIQUE NOT NULL,
        length INTEGER NOT NULL,
        definition TEXT,
        antonym TEXT
    );
    """

    sql_create_telugu_movies_table = """
    CREATE TABLE IF NOT EXISTS telugu_movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tmdb_id INTEGER UNIQUE NOT NULL,
        title TEXT NOT NULL,
        processed_title_for_game TEXT NOT NULL,
        lead_actor TEXT,
        lead_actress TEXT,
        director TEXT,
        release_date TEXT
    );
    """

    try:
        c = conn.cursor()
        print("Creating table: english_words...")
        c.execute(sql_create_english_words_table)
        print("Table english_words created successfully (if not exists).")
        
        print("Creating table: telugu_movies...")
        c.execute(sql_create_telugu_movies_table)
        print("Table telugu_movies created successfully (if not exists).")
        
        conn.commit()
    except Error as e:
        print(f"Error creating tables: {e}")

def initialize_database():
    """Initializes the database and creates tables if they don't exist."""
    conn = create_connection()
    if conn is not None:
        create_tables(conn)
        conn.close()
    else:
        print("Error! Cannot create the database connection.")

# --- Helper functions and constants (copied from app.py for standalone execution) ---
import requests
import os
import time
import re
from dotenv import load_dotenv

load_dotenv()

WORDS_API_KEY = os.getenv("WORDS_API_KEY")
WORDS_API_HOST = os.getenv("WORDS_API_HOST")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

MIN_WORD_LENGTH_API = 4
MAX_WORD_LENGTH_API = 12
MIN_MOVIE_TITLE_LENGTH = 2

MAX_API_RETRIES = 3
RETRY_DELAY_SECONDS = 2

def process_movie_title(title: str) -> str:
    if not title:
        return ""
    processed_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
    processed_title = processed_title.upper().strip()
    if len(processed_title) >= MIN_MOVIE_TITLE_LENGTH:
        return processed_title
    return ""

# --- Data Population Functions ---

def populate_english_words_from_api(conn, num_words_to_fetch=100):
    print(f"--- Starting English word population: Fetching {num_words_to_fetch} words. ---")
    if not WORDS_API_KEY or not WORDS_API_HOST:
        print("Error: WordsAPI credentials not found.")
        return

    base_url = f"https://{WORDS_API_HOST}/words/"
    headers = {"X-RapidAPI-Key": WORDS_API_KEY, "X-RapidAPI-Host": WORDS_API_HOST}
    cursor = conn.cursor()
    words_added = 0

    while words_added < num_words_to_fetch:
        try:
            # 1. Get a random word
            random_word_params = {"random": "true", "lettersMin": str(MIN_WORD_LENGTH_API), "lettersMax": str(MAX_WORD_LENGTH_API), "letterPattern": "^[a-zA-Z]+$"}
            response = requests.get(base_url, headers=headers, params=random_word_params, timeout=10)
            response.raise_for_status()
            word_data = response.json()
            word = word_data.get("word")

            if not word:
                continue

            # Check if word already exists
            cursor.execute("SELECT id FROM english_words WHERE word = ?", (word,))
            if cursor.fetchone():
                print(f"Word '{word}' already in DB. Skipping.")
                continue

            # 2. Get details for that specific word
            details_response = requests.get(f"{base_url}{word}", headers=headers, timeout=10)
            definition = None
            antonym = None

            if details_response.status_code == 200:
                details_data = details_response.json()
                if details_data.get("results"):
                    definition = details_data["results"][0].get("definition")
                if details_data.get("antonyms"):
                    antonym = details_data["antonyms"][0]

            # 3. Insert into database
            sql = ''' INSERT OR IGNORE INTO english_words(word, length, definition, antonym) VALUES(?,?,?,?) '''
            cursor.execute(sql, (word, len(word), definition, antonym))
            conn.commit()
            words_added += 1
            print(f"Added word ({words_added}/{num_words_to_fetch}): {word}")

        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}. Retrying after delay...")
            time.sleep(RETRY_DELAY_SECONDS)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

def populate_telugu_movies_from_tmdb(conn, num_pages_to_fetch=5):
    print(f"--- Starting Telugu movie population: Fetching {num_pages_to_fetch} pages. ---")
    if not TMDB_API_KEY:
        print("Error: TMDB API key not found.")
        return

    cursor = conn.cursor()
    movies_added = 0

    for page in range(1, num_pages_to_fetch + 1):
        try:
            # 1. Get a page of popular movies
            discover_url = f"{TMDB_BASE_URL}/discover/movie"
            discover_params = {"api_key": TMDB_API_KEY, "with_original_language": "te", "sort_by": "popularity.desc", "page": page}
            response = requests.get(discover_url, params=discover_params, timeout=10)
            response.raise_for_status()
            movies = response.json().get("results", [])
            print(f"Processing page {page}/{num_pages_to_fetch}, found {len(movies)} movies.")

            for movie in movies:
                tmdb_id = movie.get("id")
                title = movie.get("title")
                release_date = movie.get("release_date")

                if not tmdb_id or not title:
                    continue
                
                # Check if movie already exists
                cursor.execute("SELECT id FROM telugu_movies WHERE tmdb_id = ?", (tmdb_id,))
                if cursor.fetchone():
                    print(f"Movie '{title}' (ID: {tmdb_id}) already in DB. Skipping.")
                    continue

                # 2. Get credits for the movie
                credits_url = f"{TMDB_BASE_URL}/movie/{tmdb_id}/credits"
                credits_params = {"api_key": TMDB_API_KEY}
                credits_response = requests.get(credits_url, params=credits_params, timeout=10)
                credits_data = credits_response.json()

                director = next((p['name'] for p in credits_data.get('crew', []) if p['job'] == 'Director'), None)
                lead_actor = next((p['name'] for p in credits_data.get('cast', []) if p['gender'] == 2 and p['order'] <= 3), None)
                lead_actress = next((p['name'] for p in credits_data.get('cast', []) if p['gender'] == 1 and p['order'] <= 3), None)

                # 3. Insert into database
                processed_title = process_movie_title(title)
                if processed_title:
                    sql = ''' INSERT OR IGNORE INTO telugu_movies(tmdb_id, title, processed_title_for_game, lead_actor, lead_actress, director, release_date) VALUES(?,?,?,?,?,?,?) '''
                    cursor.execute(sql, (tmdb_id, title, processed_title, lead_actor, lead_actress, director, release_date))
                    conn.commit()
                    movies_added += 1
                    print(f"Added movie: {title}")

        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}. Skipping page {page}.")
            time.sleep(RETRY_DELAY_SECONDS)
        except Exception as e:
            print(f"An unexpected error occurred on page {page}: {e}")

def get_table_counts(conn):
    """Returns a dictionary with the counts of rows in each table."""
    counts = {}
    try:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM english_words")
        counts['english_words'] = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM telugu_movies")
        counts['telugu_movies'] = c.fetchone()[0]
    except Error as e:
        print(f"Error getting table counts: {e}")
        return {'english_words': 0, 'telugu_movies': 0}
    return counts

def get_random_english_word(conn):
    """Fetches a random word and its details from the english_words table."""
    try:
        c = conn.cursor()
        # Use ORDER BY RANDOM() to get a random row. Inefficient for huge tables, but fine for this size.
        c.execute("SELECT word, definition, antonym FROM english_words ORDER BY RANDOM() LIMIT 1")
        record = c.fetchone()
        if record:
            # Return a dictionary that matches the data structure we need
            return {
                "word": record[0],
                "hint_context": {
                    "type": "english",
                    "definition": record[1],
                    "antonym": record[2]
                }
            }
    except Error as e:
        print(f"Error fetching random English word: {e}")
    return None

def get_random_telugu_movie(conn):
    """Fetches a random movie and its details from the telugu_movies table."""
    try:
        c = conn.cursor()
        c.execute("SELECT processed_title_for_game, tmdb_id, lead_actor, lead_actress, director, release_date, title FROM telugu_movies ORDER BY RANDOM() LIMIT 1")
        record = c.fetchone()
        if record:
            return {
                "word": record[0],
                "hint_context": {
                    "type": "movie",
                    "id": record[1],
                    "actor": record[2],
                    "actress": record[3],
                    "director": record[4],
                    "release_date": record[5],
                    "original_title": record[6]
                }
            }
    except Error as e:
        print(f"Error fetching random Telugu movie: {e}")
    return None

if __name__ == '__main__':
    print("Database utility script started.")
    conn = create_connection()
    if conn:
        # You can adjust the numbers here to fetch more or less data.
        # Note: Fetching large amounts of data can take a long time and many API calls.
        populate_english_words_from_api(conn, num_words_to_fetch=50)
        populate_telugu_movies_from_tmdb(conn, num_pages_to_fetch=2) # 2 pages = ~40 movies
        conn.close()
        print("--- Population complete. ---")
    print("Database utility script finished.")
