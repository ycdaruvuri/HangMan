import React from 'react';
import './WordDisplay.css';

function WordDisplay({ wordToGuess, guessedLetters }) {
  if (!wordToGuess) {
    return <div className="word-display-container loading">Loading word...</div>;
  }

  return (
    <div className="word-display-container">
      {wordToGuess.split('').map((letter, index) => (
        <span key={index} className="letter-placeholder">
          {guessedLetters.includes(letter.toLowerCase()) ? letter.toUpperCase() : '_'}
        </span>
      ))}
    </div>
  );
}

export default WordDisplay;
