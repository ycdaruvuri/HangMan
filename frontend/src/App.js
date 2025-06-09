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
  const fetchWord = useCallback(async () => {
    setGameStatus('loading');
    setErrorMessage('');
    setWordToGuess('');
    try {
      const response = await axios.get(`${BACKEND_URL}/word`);
      const newWord = response.data.word;
      if (newWord && typeof newWord === 'string' && newWord.length > 0) {
        setWordToGuess(newWord.toLowerCase());
        setGameStatus('playing');
      } else {
        throw new Error("Invalid word received from API");
      }
    } catch (err) {
      console.error("Failed to fetch word:", err);
      setErrorMessage('Failed to fetch a new word. Using a default word.');
      const defaultWords = ["react", "python", "hangman", "cascade"];
      setWordToGuess(defaultWords[Math.floor(Math.random() * defaultWords.length)]);
      setGameStatus('playing'); // Still allow playing with default word
    }
  }, []);

  const resetGame = useCallback(() => {
    setGuessedLetters([]);
    setWrongGuesses(0);
    setHint('');
    setShowHint(false);
    setHintButtonUsed(false);
    setHintLoading(false);
    fetchWord();
  }, [fetchWord]);

  useEffect(() => {
    resetGame(); // Initial game setup
  }, [resetGame]);

  const handleGuess = useCallback((letter) => {
    if (gameStatus !== 'playing' || guessedLetters.includes(letter) || !wordToGuess) {
      return;
    }

    const newGuessedLetters = [...guessedLetters, letter];
    setGuessedLetters(newGuessedLetters);

    if (wordToGuess.includes(letter)) {
      const wordGuessed = wordToGuess
        .split('')
        .every(char => newGuessedLetters.includes(char.toLowerCase()));
      if (wordGuessed) {
        setGameStatus('won');
      }
    } else {
      const newWrongGuesses = wrongGuesses + 1;
      setWrongGuesses(newWrongGuesses);
      if (newWrongGuesses >= MAX_WRONG_GUESSES) {
        setGameStatus('lost');
      }
    }
  }, [wordToGuess, guessedLetters, wrongGuesses, gameStatus]);

  const handleShowHint = useCallback(async () => {
    if (!wordToGuess || hintButtonUsed) return;

    setHintLoading(true);
    setHint('');
    setShowHint(true); // Show the area where hint/loading message will appear

    try {
      const response = await axios.get(`${BACKEND_URL}/word/${wordToGuess}/definitions`);
      if (response.data && response.data.definition) {
        setHint(response.data.definition);
      } else {
        setHint('No definition found for this word.');
      }
    } catch (error) {
      console.error("Failed to fetch hint:", error);
      if (error.response && error.response.data && error.response.data.detail) {
        setHint(`Hint Error: ${error.response.data.detail}`);
      } else {
        setHint('Could not fetch hint at this time.');
      }
    }
    setHintButtonUsed(true);
    setHintLoading(false);
  }, [wordToGuess, hintButtonUsed]);

  let statusDisplayMessage = '';
  let statusClass = '';

  if (gameStatus === 'loading') {
    statusDisplayMessage = 'Loading game...';
  } else if (errorMessage) {
    statusDisplayMessage = errorMessage;
    statusClass = 'error';
  } else if (gameStatus === 'won') {
    statusDisplayMessage = 'Congratulations! You won!';
    statusClass = 'win';
  } else if (gameStatus === 'lost') {
    statusDisplayMessage = `Game Over! The word was: ${wordToGuess.toUpperCase()}`;
    statusClass = 'lose';
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>Hangman Game</h1>
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

        {(gameStatus === 'won' || gameStatus === 'lost' || (errorMessage && gameStatus !== 'loading')) && (
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
