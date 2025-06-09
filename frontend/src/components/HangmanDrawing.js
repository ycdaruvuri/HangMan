import React from 'react';
import './HangmanDrawing.css';

const HEAD = (
  <div key="head" className="hangman-part head" />
);

const BODY = (
  <div key="body" className="hangman-part body" />
);

const RIGHT_ARM = (
  <div key="right-arm" className="hangman-part right-arm" />
);

const LEFT_ARM = (
  <div key="left-arm" className="hangman-part left-arm" />
);

const LEFT_LEG = (
  <div key="left-leg" className="hangman-part left-leg" />
);

const RIGHT_LEG = (
  <div key="right-leg" className="hangman-part right-leg" />
);

// Order for 6 wrong guesses: Head, Body, Left Arm, Right Arm, Left Leg, Right Leg
const BODY_PARTS = [HEAD, BODY, LEFT_ARM, RIGHT_ARM, LEFT_LEG, RIGHT_LEG];

function HangmanDrawing({ numberOfWrongGuesses }) {
  return (
    <div className="hangman-drawing-container">
      {/* Gallow structure - always visible */}
      <div className="gallow-rope" />
      <div className="gallow-top" />
      <div className="gallow-pole" />
      <div className="gallow-base" />

      {/* Hangman body parts - displayed based on wrong guesses */}
      {BODY_PARTS.slice(0, numberOfWrongGuesses).map((part, index) => (
        <React.Fragment key={index}>{part}</React.Fragment>
      ))}
    </div>
  );
}

export default HangmanDrawing;
