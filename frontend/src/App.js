import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './App.css';
import HangmanDrawing from './components/HangmanDrawing';
import WordDisplay from './components/WordDisplay';
import Keyboard from './components/Keyboard';

const MAX_WRONG_GUESSES = 6;
const BACKEND_URL = 'http://127.0.0.1:8000';

function App() {
  const [wordToGuess, setWordToGuess] = useState('');
  const [guessedLetters, setGuessedLetters] = useState([]);
  const [wrongGuesses, setWrongGuesses] = useState(0);
  const [gameStatus, setGameStatus] = useState('playing'); // 'playing', 'won', 'lost', 'loading', 'error'
  const [hint, setHint] = useState('');
  const [showHint, setShowHint] = useState(false);
  const [hintButtonUsed, setHintButtonUsed] = useState(false);
  const [hintLoading, setHintLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('english'); // 'english' or 'telugu_movies'
  const [hintContext, setHintContext] = useState(null); // To store movie ID or other hint context

  const playSound = useCallback((soundFile) => {
    try {
      // Sounds are in the public folder, so the path is relative to the root.
      const sound = new Audio(`/${soundFile}`);
      sound.play().catch(error => {
        // Autoplay was prevented or another error occurred
        if (error.name === 'NotAllowedError') {
          // Log a less intrusive message or do nothing
          console.log(`Autoplay prevented for ${soundFile}. User interaction needed.`);
        } else {
          // Log other errors normally
          console.error(`Could not play sound: ${soundFile}`, error);
        }
      });
    } catch (error) {
      // This outer catch is for errors during new Audio() instantiation, etc.
      console.error(`Error initializing sound ${soundFile}:`, error);
    }
  }, []);
  const fetchWord = useCallback(async (category) => {
    setGameStatus('loading');
    setErrorMessage('');
    setWordToGuess('');
    setHintContext(null); // Reset hint context on new word fetch

    try {
      const response = await axios.get(`${BACKEND_URL}/word?category=${category}`);
      const { word, hint_context } = response.data;
      if (word && typeof word === 'string' && word.length > 0) {
        setWordToGuess(word.toLowerCase());
        setHintContext(hint_context || null); // Store the entire hint context object
        setGameStatus('playing');
      } else {
        throw new Error("Invalid data received from server");
      }
    } catch (err) {
      console.error("Failed to fetch word:", err);
      // Display specific error from backend if available, otherwise generic message
      const detail = err.response?.data?.detail;
      if (detail) {
        setErrorMessage(detail);
      } else {
        setErrorMessage('Failed to fetch a new word. The server might be down.');
      }
      setGameStatus('error'); // Set a distinct error status
    }
  }, []); // No dependencies needed as category is passed in

  const resetGame = useCallback(() => {
    setGuessedLetters([]);
    setWrongGuesses(0);
    setHint('');
    setShowHint(false);
    setHintButtonUsed(false);
    setHintLoading(false);
    setHintContext(null); // Also reset hint context
    fetchWord(selectedCategory); // Pass current category to fetchWord
  }, [fetchWord, selectedCategory]);

  useEffect(() => {
    // On initial load, fetch word with default category
    fetchWord(selectedCategory);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only on mount to fetch initial word

  // Separate useEffect for resetting game when category changes AFTER initial load
  useEffect(() => {
    // Avoid resetting on initial mount if fetchWord already ran
    // This effect is specifically for when user *changes* the category
    if (wordToGuess) { // Check if a word already exists (i.e., not initial load)
        console.log(`Category changed to: ${selectedCategory}, resetting game.`);
        resetGame();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCategory]); // resetGame dependency will be handled by its own useCallback

  const handleGuess = useCallback((letter) => {
    const lowerCaseLetter = letter.toLowerCase();
    // Prevent guessing if game is not in play or letter has been guessed
    if (gameStatus !== 'playing' || guessedLetters.includes(lowerCaseLetter)) {
      return;
    }

    setGuessedLetters(prev => [...prev, lowerCaseLetter]);

    if (wordToGuess.toLowerCase().includes(lowerCaseLetter)) {
      playSound('sounds/correct.mp3');
    } else {
      setWrongGuesses(prev => prev + 1);
      playSound('sounds/incorrect.mp3');
    }
  }, [gameStatus, guessedLetters, wordToGuess, playSound]);

  // Effect to check for win/loss condition
  useEffect(() => {
    if (gameStatus !== 'playing') return;

    const isWinner = wordToGuess
      .toLowerCase()
      .split('')
      .every(char => guessedLetters.includes(char) || char === ' ');

    if (isWinner) {
      setGameStatus('win');
    } else if (wrongGuesses >= MAX_WRONG_GUESSES) {
      setGameStatus('lose');
    }
  }, [guessedLetters, wrongGuesses, wordToGuess, gameStatus]);

  // Effect to play sounds on win/loss
  useEffect(() => {
    if (gameStatus === 'win') {
      playSound('sounds/win.mp3');
    } else if (gameStatus === 'lose') {
      playSound('sounds/lose.mp3');
    }
  }, [gameStatus, playSound]);

  const handleShowHint = useCallback(() => {
    if (!wordToGuess || hintButtonUsed) return;

    // Guard against showing hint if context is not available
    if (!hintContext) {
      setHint('No hint is available for this word.');
      setShowHint(true);
      setHintButtonUsed(true);
      return;
    }

    setHintLoading(true);
    setShowHint(true);

    const possibleHints = [];
    // For English Words
    if (hintContext.definition) {
      possibleHints.push(`Definition: ${hintContext.definition}`);
    }
    if (hintContext.antonym) {
      possibleHints.push(`Antonym: ${hintContext.antonym}`);
    }
    // For Telugu Movies
    if (hintContext.lead_actor) {
      possibleHints.push(`Lead Actor: ${hintContext.lead_actor}`);
    }
    if (hintContext.lead_actress) {
      possibleHints.push(`Lead Actress: ${hintContext.lead_actress}`);
    }
    if (hintContext.director) {
      possibleHints.push(`Director: ${hintContext.director}`);
    }
    if (hintContext.release_date) {
      possibleHints.push(`Released on: ${hintContext.release_date}`);
    }

    if (possibleHints.length > 0) {
      // Select a random hint from the available options
      const randomIndex = Math.floor(Math.random() * possibleHints.length);
      setHint(possibleHints[randomIndex]);
    } else {
      setHint('No specific hint found, try your best!');
    }

    setHintButtonUsed(true);
    setHintLoading(false);
  }, [wordToGuess, hintButtonUsed, hintContext]);

  let statusDisplayMessage = '';
  let statusClass = '';

  if (gameStatus === 'loading') {
    statusDisplayMessage = 'Loading game...';
  } else if (errorMessage) {
    statusDisplayMessage = errorMessage;
    statusClass = 'error';
  } else if (gameStatus === 'win') {
    statusDisplayMessage = 'Congratulations! You won!';
    statusClass = 'win';
  } else if (gameStatus === 'lose') {
    statusDisplayMessage = `Game Over! The word was: ${wordToGuess.toUpperCase()}`;
    statusClass = 'lose';
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>Hangman Game</h1>
        <div className="category-selector">
          <label>Choose Category: </label>
          <button 
            onClick={() => setSelectedCategory('english')} 
            className={selectedCategory === 'english' ? 'active' : ''}
            disabled={gameStatus === 'loading'}
          >
            English Words
          </button>
          <button 
            onClick={() => setSelectedCategory('telugu_movies')} 
            className={selectedCategory === 'telugu_movies' ? 'active' : ''}
            disabled={gameStatus === 'loading'}
          >
            Telugu Movies
          </button>
        </div>
      </header>
      <div className="game-area">
        <HangmanDrawing numberOfWrongGuesses={wrongGuesses} />
        <WordDisplay wordToGuess={wordToGuess} guessedLetters={guessedLetters} />

        {gameStatus === 'playing' && !hintButtonUsed && (
          <button onClick={handleShowHint} className="hint-button" disabled={hintLoading || !wordToGuess}>
            {hintLoading ? 'Getting Hint...' : '🔍 Show Hint'}
          </button>
        )}

        {showHint && (
          <div className="hint-display">
            {hintLoading ? <p>Loading hint...</p> : <p>{hint}</p>}
          </div>
        )}
        
        {statusDisplayMessage && (
          <p className={`status-message ${statusClass}`}>
            {statusDisplayMessage}
          </p>
        )}

        {gameStatus === 'playing' && (
          <Keyboard
            onLetterClick={handleGuess}
            guessedLetters={guessedLetters}
            disabled={gameStatus !== 'playing'}
          />
        )}

        {(gameStatus === 'win' || gameStatus === 'lose' || (errorMessage && gameStatus !== 'loading')) && (
          <button onClick={resetGame} className="reset-button" disabled={gameStatus === 'loading'}>
            {gameStatus === 'loading' ? 'Loading...' : 'Play Again'}
          </button>
        )}

        {gameStatus === 'playing' && (
            <p className="wrong-guesses">Wrong Guesses: {wrongGuesses} / {MAX_WRONG_GUESSES}</p>
        )}
        
      </div>
    </div>
  );
}

export default App;
