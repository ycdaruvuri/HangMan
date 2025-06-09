# Hangman Game

This project is a classic Hangman game with a Python Flask backend and a React frontend.

## Project Structure

-   `backend/`: Contains the Python Flask server.
    -   `app.py`: The main Flask application.
    -   `requirements.txt`: Python dependencies.
    -   `README.md`: Backend-specific instructions.
-   `frontend/`: Contains the React application.
    -   `README.md`: Frontend-specific instructions.

## Game Description

-   The game randomly selects a word.
-   The user guesses one letter at a time.
-   If the letter exists in the word, its position(s) are revealed.
-   If the letter doesn't exist, the number of wrong guesses increases.
-   The player loses if they make 5 wrong guesses.
-   The player wins if they guess the word before reaching 5 wrong attempts.

## Setup and Running

Follow the instructions in the `backend/README.md` and `frontend/README.md` to set up and run the respective parts of the application.
