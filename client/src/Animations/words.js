// JSON-based word loading system
// All word animations are loaded from wordsData.json
import { loadAllWords, getAvailableWordsFromJSON } from './Utils/wordLoader';

// Load all words from JSON
const loadedWords = loadAllWords();

// Named exports for backward compatibility (all 91 words from wordsData.json)
export const { TIME, HOME, PERSON, YOU, HELLO, THANK, PLEASE, SORRY, YES, NO,
  HELP, NAME, FAMILY, FRIEND, WORK, SCHOOL, EAT, DRINK, GOOD, BAD,
  ME, WATER, MOTHER, FATHER, BROTHER, SISTER, TEACHER, FOOD, HAPPY, SAD,
  WHERE, UNDERSTAND, PLEASE_NAMASTE,
  I, LOVE, COME, GO, WANT, KNOW, TODAY, TOMORROW, YESTERDAY,
  MORNING, NIGHT, STOP, SLEEP, TIRED, SICK,
  BYE, WELCOME, AGAIN, WHY, HOW, SEE, CAN, HI,
  NOW, LATER, WAIT, FINISH, LIKE, DO, READ, MONEY, PLAY,
  WHAT, WHEN, WHO, WHICH,
  // Negations
  NOT, NEVER, LIVE,
  // Pronouns
  HE, SHE, IT,
  // Emotions & states
  ANGRY, SCARED, HUNGRY, THIRSTY, BORED, EXCITED,
  // Directions & positions
  LEFT, RIGHT, UP, DOWN, NEAR, FAR, FRONT, BACK, INSIDE } = loadedWords;

// DON'T cannot be a valid JS identifier due to the apostrophe; export as DONT
export const DONT = loadedWords["DON'T"];

// Dynamic lookup: returns the animation function for any word in wordsData.json,
// including words added in the future without needing to update this file.
export const getWordAnimation = (word) => {
  const upper = word.toUpperCase();
  // Try exact match first (handles contractions like "DON'T")
  if (loadedWords[upper]) return loadedWords[upper];
  // Fallback: strip non-alpha characters (legacy behaviour)
  const clean = upper.replace(/[^A-Z]/g, '');
  return loadedWords[clean] || null;
};

// Full list of available words (automatically generated from JSON)
export const wordList = getAvailableWordsFromJSON();
