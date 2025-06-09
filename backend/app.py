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
WORDS_API_HOST = os.getenv("WORDS_API_HOST", "wordsapiv1.p.rapidapi.com")

MIN_WORD_LENGTH_API = 4
MAX_WORD_LENGTH_API = 10

MAX_API_RETRIES = 1 # Reduced retries
RETRY_DELAY_SECONDS = 1

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
async def get_word_endpoint():
    word_data = get_word_from_wordsapi()
    if word_data and word_data.get("word"):
        # word_data will now be like {"word": "example"}
        return word_data 
    else:
        # If MAX_API_RETRIES is 1, "multiple attempts" might be misleading, but the core issue is failure.
        raise HTTPException(status_code=503, detail="Could not retrieve a word from the external API.")

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
