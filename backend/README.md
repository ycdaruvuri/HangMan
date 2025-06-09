# Hangman Game - Backend

This directory contains the Python FastAPI backend for the Hangman game.

## Setup

1.  Navigate to the `backend` directory.
2.  Create a virtual environment (if you haven't already):
    ```bash
    python -m venv venv
    ```
3.  Activate the virtual environment:
    *   Windows: `venv\Scripts\activate`
    *   macOS/Linux: `source venv/bin/activate`
4.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    This will install FastAPI, Uvicorn, Requests, and python-dotenv.

## API Key Configuration (WordsAPI)

This backend uses WordsAPI (via RapidAPI) to fetch random words. You will need an API key to use it.

1.  **Sign up/Log in to RapidAPI:** Go to [RapidAPI](https://rapidapi.com) and create an account or log in.
2.  **Subscribe to WordsAPI:** Search for "WordsAPI" on RapidAPI (usually by `dpventures`) and subscribe to the API. Choose a plan that suits your needs (there's typically a free tier with limitations).
3.  **Get your API Key:** Once subscribed, you'll find your `X-RapidAPI-Key` in the API dashboard or code snippets section for WordsAPI.
4.  **Create `.env` file:**
    In the `backend` directory, create a new file named `.env` by copying the example file:
    ```bash
    # On Windows (Command Prompt)
    copy .env.example .env
    # On macOS/Linux (bash)
    # cp .env.example .env
    ```
5.  **Set Environment Variables:** Open the newly created `.env` file and replace `"YOUR_X_RAPIDAPI_KEY_HERE"` with your actual `X-RapidAPI-Key`. Ensure the `WORDS_API_HOST` is also correct (usually `wordsapiv1.p.rapidapi.com`).
    The file should look similar to this:
    ```env
    WORDS_API_KEY="your_actual_X-RapidAPI-Key_here"
    WORDS_API_HOST="wordsapiv1.p.rapidapi.com"
    # Optional: FRONTEND_URL="http://localhost:3001"
    ```
    The application uses `python-dotenv` to load these variables from the `.env` file when it starts.
    **Important:** The `.env` file is listed in `.gitignore` (or should be) and must NOT be committed to your Git repository, as it contains sensitive credentials.

## Running the Development Server

Once the virtual environment is activated and dependencies are installed, run the FastAPI development server using Uvicorn:

```bash
uvicorn app:app --reload --port 8000
```

Breakdown of the command:
- `uvicorn`: The ASGI server.
- `app:app`: Tells Uvicorn to look for an object named `app` (the FastAPI instance) inside a file named `app.py`.
- `--reload`: Enables auto-reloading. The server will restart automatically when you save changes to your code. Ideal for development.
- `--port 8000`: Specifies that the server should run on port 8000.

The server will start on `http://127.0.0.1:8000` by default. You can access the API documentation (Swagger UI) at `http://127.0.0.1:8000/docs` in your browser.