from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn
import os
from dotenv import load_dotenv
import time # Added for retry delay

# Load environment variables from .env file
load_dotenv()

import database_utils

app = FastAPI()

# Initialize the database and create tables on startup
print("Initializing database...")
database_utils.initialize_database()
print("Database initialization complete.")

# Verify database content on startup
print("Verifying database content...")
conn = database_utils.create_connection()
if conn:
    counts = database_utils.get_table_counts(conn)
    print(f"--> Cache status: {counts.get('english_words', 0)} English words, {counts.get('telugu_movies', 0)} Telugu movies.")
    conn.close()

# Configure CORS
origins = [
    os.getenv("FRONTEND_URL", "http://localhost:3000"), # Allow configuring frontend URL via .env
    "http://127.0.0.1:3000",
]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


WORDS_API_KEY = os.getenv("WORDS_API_KEY")
WORDS_API_HOST = os.getenv("WORDS_API_HOST")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

MIN_WORD_LENGTH_API = 4
MAX_WORD_LENGTH_API = 10

MAX_API_RETRIES = 1 # Max number of retries for external APIs

# Constants for TMDB
TMDB_BASE_URL = "https://api.themoviedb.org/3"
MIN_MOVIE_TITLE_LENGTH = 3
MAX_MOVIE_TITLE_LENGTH = 30 # Adjust as needed for playability

RETRY_DELAY_SECONDS = 1
import re # For processing movie titles
import random # For selecting random movie/page

def process_movie_title(title: str) -> str:
    """
    Processes a movie title for Hangman:
    - Converts to uppercase.
    - Removes characters that are not alphanumeric or space.
    - Ensures it's within reasonable length limits.
    - Trims leading/trailing whitespace.
    """
    if not title:
        return ""
    
    # Keep alphanumeric and spaces, remove others. Allow basic punctuation if desired.
    processed_title = re.sub(r'[^a-zA-Z0-9\s]', '', title) # Example: only letters, numbers, spaces
    processed_title = processed_title.upper()
    
    # Trim and ensure it's not just spaces or empty after processing
    processed_title = processed_title.strip()
    if not processed_title:
        return ""

    # Optional: Collapse multiple spaces to one, though Hangman can reveal multiple spaces
    # processed_title = re.sub(r'\s+', ' ', processed_title)

    # We only check for a minimum length to avoid empty or junk titles.
    # The maximum length check is removed as per the new requirement.
    if len(processed_title) >= MIN_MOVIE_TITLE_LENGTH:
        return processed_title
    return ""

# --- Main Word Fetching Endpoint ---

@app.get("/word")
async def get_word(category: str = 'english'):
    """
    Fetches a word from the database cache.
    This is the primary endpoint for starting a new game round.
    It returns the word to guess and a rich context object for hints.
    """
    word_data = None
    # Establish a connection to the database for this request
    conn = database_utils.create_connection()
    if not conn:
        # If the database file can't be accessed, it's a server error.
        raise HTTPException(status_code=500, detail="Could not connect to the database.")

    try:
        print(f"Request received for category: '{category}'. Fetching from cache...")
        if category == 'english':
            word_data = database_utils.get_random_english_word(conn)
        elif category == 'telugu_movies':
            word_data = database_utils.get_random_telugu_movie(conn)
        else:
            # Handle invalid category requests from the client.
            raise HTTPException(status_code=400, detail=f"Invalid category: '{category}'.")

        # This is the "cache miss" scenario.
        if not word_data:
            print(f"CACHE MISS: No data found in the database for category '{category}'.")
            # We inform the user to run the population script.
            # A more advanced version could fall back to an API call here.
            raise HTTPException(
                status_code=404, 
                detail=f"Cache empty for '{category}'. Please run the population script (database_utils.py)."
            )
        
        print(f"CACHE HIT: Successfully fetched '{word_data.get('word')}' for category '{category}'.")
        # The data from the database is already in the correct format.
        return word_data

    except Exception as e:
        # Catch any other unexpected errors during the process.
        print(f"An unexpected server error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
    finally:
        # CRITICAL: Always ensure the database connection is closed.
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
