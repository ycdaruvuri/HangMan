from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn
import os
from dotenv import load_dotenv
import time # Added for retry delay

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Configure CORS
origins = [
    os.getenv("FRONTEND_URL", "http://localhost:3000"), # Allow configuring frontend URL via .env
    "http://127.0.0.1:3000",
]

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

    if MIN_MOVIE_TITLE_LENGTH <= len(processed_title) <= MAX_MOVIE_TITLE_LENGTH:
        return processed_title
    return ""

def get_telugu_movie_from_tmdb():
    if not TMDB_API_KEY:
        print("Error: TMDB_API_KEY not configured in .env file.")
        return None

    url = f"{TMDB_BASE_URL}/discover/movie"
    # Fetch from a few pages to get variety but prioritize popular ones
    # TMDB pages are 1-indexed
    page_to_fetch = random.randint(1, 5) 
    params = {
        "api_key": TMDB_API_KEY,
        "with_original_language": "te",
        "sort_by": "popularity.desc",
        "page": page_to_fetch,
        "include_adult": "false" # Explicitly exclude adult content
    }
    
    print(f"Fetching Telugu movies from TMDB: {url} with params: {params}")
    
    for attempt in range(MAX_API_RETRIES):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = data.get("results")

            if results:
                valid_movies = []
                for movie in results:
                    title = movie.get("original_title") or movie.get("title")
                    movie_id = movie.get("id")
                    
                    if title and movie_id:
                        processed_title = process_movie_title(title)
                        if processed_title and any(char.isalpha() for char in processed_title):
                            valid_movies.append({"title": processed_title, "id": movie_id})
                
                if valid_movies:
                    selected_movie = random.choice(valid_movies)
                    print(f"Successfully fetched and processed Telugu movie: {selected_movie}")
                    return {"word": selected_movie['title'], "id": selected_movie['id']} 
            
            error_detail = data.get("status_message", "No suitable movie titles found") if results is None or not valid_titles else "No suitable movie titles found"
            print(f"{error_detail} in TMDB response on attempt {attempt + 1}. Page: {page_to_fetch}. Results count: {len(results) if results else 0}")

        except requests.exceptions.Timeout:
            print(f"TMDB API request timed out on attempt {attempt + 1}.")
        except requests.exceptions.RequestException as e:
            status_code = e.response.status_code if e.response is not None else "N/A"
            error_msg = str(e)
            if e.response is not None:
                try:
                    error_msg = e.response.json().get("status_message", str(e))
                except ValueError: # Not JSON response
                    error_msg = e.response.text[:200] # First 200 chars of non-JSON error
            print(f"TMDB API request failed on attempt {attempt + 1}. Status: {status_code}. Error: {error_msg}")
        except Exception as e:
            print(f"An unexpected error occurred fetching from TMDB on attempt {attempt + 1}: {e}")
        
        if attempt < MAX_API_RETRIES - 1:
            print(f"Retrying TMDB fetch in {RETRY_DELAY_SECONDS} seconds...")
            time.sleep(RETRY_DELAY_SECONDS)
            
    return None

def get_word_from_wordsapi():
    if not WORDS_API_KEY or not WORDS_API_HOST:
        print("Error: WordsAPI key or host not configured in .env file.")
        return None

    url = f"https://{WORDS_API_HOST}/words/"
    headers = {
        "X-RapidAPI-Key": WORDS_API_KEY,
        "X-RapidAPI-Host": WORDS_API_HOST
    }
    querystring = {
        "random": "true",
        "lettersMin": str(MIN_WORD_LENGTH_API),
        "lettersMax": str(MAX_WORD_LENGTH_API),
        "letterPattern": "^[a-zA-Z]+$" # Ensures word is purely alphabetic
    }

    for attempt in range(MAX_API_RETRIES):
        try:
            print(f"Attempt {attempt + 1}/{MAX_API_RETRIES} - Fetching word from WordsAPI: {url} with params {querystring}")
            response = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            data = response.json()
            word = data.get("word")
            
            if word and isinstance(word, str) and word.isalpha():
                if ' ' not in word and MIN_WORD_LENGTH_API <= len(word) <= MAX_WORD_LENGTH_API:
                    print(f"Successfully fetched API word: {word.lower()}")
                    return {"word": word.lower()} # Return only the word
                else:
                    print(f"WordsAPI returned an unsuitable word: '{word}'. Retrying if possible.")
            else:
                print(f"WordsAPI did not return a valid word string or word was unsuitable. Response: {data}. Retrying if possible.")

        except requests.exceptions.Timeout:
            print(f"WordsAPI request timed out on attempt {attempt + 1}.")
        except requests.exceptions.RequestException as e:
            print(f"WordsAPI request failed on attempt {attempt + 1}: {e}. Response: {e.response.text if e.response else 'No response text'}")
        except Exception as e:
            print(f"An unexpected error occurred on attempt {attempt + 1} while fetching from WordsAPI: {e}")
        
        if attempt < MAX_API_RETRIES - 1: # This condition will be false if MAX_API_RETRIES is 1
            print(f"Waiting {RETRY_DELAY_SECONDS}s before next attempt...")
            time.sleep(RETRY_DELAY_SECONDS)
        # else: # No need for 'else' if MAX_API_RETRIES is 1, loop finishes
            # print("API attempt failed.") # Covered by loop finishing
            
    print("All API attempts failed to fetch a word.")
    return None

@app.get("/word")
async def get_word_endpoint(category: str = "english"):
    print(f"Received request for category: {category}")
    word_data = None
    error_detail = "Could not retrieve a suitable word/phrase."

    if category.lower() == "english":
        word_info = get_word_from_wordsapi()
        if word_info:
            # For English words, hint context is not needed as it's fetched by word.
            word_data = {"word": word_info["word"]}
        else:
            error_detail = "Failed to retrieve an English word from WordsAPI."

    elif category.lower() == "telugu_movies":
        movie_data = get_telugu_movie_from_tmdb()
        if movie_data:
            # For movies, we package the ID so the frontend knows how to get a hint.
            word_data = {
                "word": movie_data["word"],
                "hint_context": {"type": "movie", "id": movie_data["id"]}
            }
        else:
            error_detail = "Failed to retrieve a Telugu movie title from TMDB."
    else:
        raise HTTPException(status_code=400, detail=f"Invalid category specified: {category}. Supported categories: 'english', 'telugu_movies'.")

    # This is the single point of return for all successful requests.
    if word_data:
        print(f"BACKEND LOG: Sending final response to frontend: {word_data}")
        return word_data
    else:
        # This is the single point of failure if no data was retrieved.
        print(f"Final attempt failed for category '{category}'. Error: {error_detail}")
        raise HTTPException(status_code=503, detail=error_detail)

@app.get("/movie/{movie_id}/hint")
async def get_movie_hint_endpoint(movie_id: int):
    if not TMDB_API_KEY:
        raise HTTPException(status_code=500, detail="TMDB API key not configured on server.")

    url = f"{TMDB_BASE_URL}/movie/{movie_id}/credits"
    params = {"api_key": TMDB_API_KEY}
    
    print(f"Fetching credits for movie ID: {movie_id}")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        cast = data.get("cast", [])
        crew = data.get("crew", [])
        
        possible_hints = []

        # Get main actors
        main_actors = [actor for actor in cast if actor.get("known_for_department") == "Acting" and actor.get("order") <= 4]
        for actor in main_actors:
            if actor.get("name"):
                possible_hints.append(f"Hint: Starring {actor['name']}.")

        # Get director
        directors = [member for member in crew if member.get("job") == "Director"]
        for director in directors:
            if director.get("name"):
                possible_hints.append(f"Hint: Directed by {director['name']}.")

        if possible_hints:
            selected_hint = random.choice(possible_hints)
            return {"hint": selected_hint}

        # Fallback if no specific hints found but cast exists
        if cast:
            any_actor = random.choice([actor for actor in cast if actor.get("name")])
            if any_actor:
                 return {"hint": f"Hint: One of the cast members is {any_actor['name']}."}

        raise HTTPException(status_code=404, detail="Could not find cast or crew information for this movie.")

    except requests.exceptions.RequestException as e:
        print(f"TMDB API request for credits failed: {e}")
        raise HTTPException(status_code=503, detail="Failed to fetch hint from external API.")
    except Exception as e:
        print(f"An unexpected error occurred fetching movie hint: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred while fetching the hint.")

@app.get("/word/{word_to_define}/definitions")
async def get_word_definition_endpoint(word_to_define: str):
    if not WORDS_API_KEY or not WORDS_API_HOST:
        print("Error: WordsAPI key or host not configured in .env file.")
        raise HTTPException(status_code=500, detail="API configuration error.")

    url = f"https://{WORDS_API_HOST}/words/{word_to_define}/definitions"
    headers = {
        "X-RapidAPI-Key": WORDS_API_KEY,
        "X-RapidAPI-Host": WORDS_API_HOST
    }

    try:
        print(f"Fetching definitions for '{word_to_define}' from WordsAPI: {url}")
        response = requests.request("GET", url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        data = response.json()
        definitions = data.get("definitions")

        if definitions and isinstance(definitions, list) and len(definitions) > 0:
            first_definition = definitions[0].get("definition")
            if first_definition:
                print(f"Successfully fetched definition for '{word_to_define}': {first_definition}")
                return {"word": word_to_define, "definition": first_definition}
            else:
                print(f"No definition content found in the first result for '{word_to_define}'. Definitions: {definitions}")
                raise HTTPException(status_code=404, detail=f"Definition content not found for '{word_to_define}'.")
        else:
            print(f"No definitions array found or empty for '{word_to_define}'. Response: {data}")
            raise HTTPException(status_code=404, detail=f"No definitions found for '{word_to_define}'.")

    except requests.exceptions.Timeout:
        print(f"WordsAPI request timed out for definitions of '{word_to_define}'.")
        raise HTTPException(status_code=504, detail="API request timed out.")
    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response is not None else 503
        # Avoid showing generic 404 if word itself is not in WordsAPI for definitions endpoint
        if status_code == 404 and e.response is not None and e.response.json().get("success") == False:
             print(f"WordsAPI indicated word '{word_to_define}' not found for definitions. Error: {e.response.json().get('message', 'Unknown error')}")
             raise HTTPException(status_code=404, detail=f"Word '{word_to_define}' not found in dictionary for definitions.")
        print(f"WordsAPI request failed for definitions of '{word_to_define}': {e}. Response: {e.response.text if e.response else 'No response text'}")
        raise HTTPException(status_code=status_code, detail="Failed to retrieve definitions from external API.")
    except Exception as e:
        print(f"An unexpected error occurred while fetching definitions for '{word_to_define}': {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
