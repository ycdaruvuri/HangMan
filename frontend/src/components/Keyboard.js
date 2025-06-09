import React from 'react';
import './Keyboard.css';

const ALPHABET = 'abcdefghijklmnopqrstuvwxyz'.split('');

function Keyboard({ onLetterClick, guessedLetters, disabled }) {
  return (
    <div className="keyboard-container">
      {ALPHABET.map(letter => {
        const isGuessed = guessedLetters.includes(letter);
        return (
          <button
            key={letter}
            className={`key ${isGuessed ? 'guessed' : ''}`}
            onClick={() => onLetterClick(letter)}
            disabled={isGuessed || disabled}
          >
            {letter.toUpperCase()}
          </button>
        );
      })}
    </div>
  );
}

export default Keyboard;
