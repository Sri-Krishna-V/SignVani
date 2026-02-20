import * as alphabets from './alphabets';
import * as words from './words';
import { getWordAnimation } from './words';

/**
 * Animation Player - Centralized animation playback utility
 * Provides a clean interface for triggering alphabet and word animations
 */

/**
 * Play animation for a single character
 * @param {Object} ref - Reference object from useThreeScene hook
 * @param {string} character - Single character to animate (A-Z)
 * @returns {boolean} - True if animation was queued successfully
 */
export const playAnimation = (ref, character) => {
  const upperChar = character.toUpperCase();
  
  // Validate input
  if (!ref || !ref.animations) {
    console.error('Invalid ref object provided to playAnimation');
    return false;
  }
  
  if (upperChar.length !== 1 || !/[A-Z]/.test(upperChar)) {
    console.warn(`Invalid character for animation: ${character}`);
    return false;
  }
  
  // Check if character animation exists
  if (!alphabets[upperChar]) {
    console.warn(`No animation found for character: ${upperChar}`);
    return false;
  }
  
  // Execute animation function
  alphabets[upperChar](ref);
  
  // Start animation if not already running
  if (ref.animate && ref.pending === false && ref.animations.length > 0) {
    ref.pending = true;
    ref.animate();
  }
  
  return true;
};

/**
 * Play animation for a word
 * @param {Object} ref - Reference object from useThreeScene hook
 * @param {string} word - Word to animate (checks for predefined word animations)
 * @returns {boolean} - True if word animation was found and queued
 */
export const playWord = (ref, word) => {
  const upperWord = word.toUpperCase();
  const cleanWord = upperWord.replace(/[^A-Z]/g, '');
  
  // Validate input
  if (!ref || !ref.animations) {
    console.error('Invalid ref object provided to playWord');
    return false;
  }
  
  // Check if word animation exists (named export or dynamic lookup)
  const wordAnim = words[cleanWord] || getWordAnimation(cleanWord);
  if (!wordAnim) {
    console.warn(`No animation found for word: ${cleanWord}`);
    return false;
  }
  
  // Execute word animation function
  wordAnim(ref);
  
  // Start animation if not already running
  if (ref.animate && ref.pending === false && ref.animations.length > 0) {
    ref.pending = true;
    ref.animate();
  }
  
  return true;
};

/**
 * Play animations for a string of text
 * Automatically handles words and falls back to letter-by-letter for unknown words
 * 
 * @param {Object} ref - Reference object from useThreeScene hook
 * @param {string} inputString - Text to animate
 * @param {boolean} addTextMarkers - Whether to add text update markers (default: true)
 * @returns {boolean} - True if any animations were queued
 */
export const playString = (ref, inputString, addTextMarkers = true) => {
  // Validate input
  if (!ref || !ref.animations) {
    console.error('Invalid ref object provided to playString');
    return false;
  }
  
  if (!inputString || typeof inputString !== 'string') {
    console.warn('Invalid input string provided to playString');
    return false;
  }
  
  // Validate input contains only letters, spaces, and basic punctuation
  if (!validateInput(inputString)) {
    throw new Error(
      'Input contains invalid characters. Only letters (A-Z), spaces, and basic punctuation (. , ! ?) are allowed.'
    );
  }
  
  // Sanitize and limit length for performance (especially on Raspberry Pi)
  const sanitized = inputString.trim().slice(0, 500);
  
  if (sanitized.length === 0) {
    throw new Error('Please enter some text to animate');
  }
  
  const wordArray = sanitized.toUpperCase().split(' ');
  let animationsQueued = false;
  
  for (const word of wordArray) {
    // Skip empty strings from multiple spaces
    if (word.length === 0) continue;

    // Strip punctuation so "HELLO." matches "HELLO" in wordsData.json
    const cleanWord = word.replace(/[^A-Z]/g, '');
    if (cleanWord.length === 0) continue;
    
    // Try to play as a complete word animation first (named export or dynamic lookup)
    const wordAnim = words[cleanWord] || getWordAnimation(cleanWord);
    if (wordAnim) {
      if (addTextMarkers) {
        ref.animations.push(['add-text', cleanWord + ' ']);
      }
      wordAnim(ref);
      animationsQueued = true;
    } 
    // Fall back to letter-by-letter fingerspelling
    else {
      for (const [index, ch] of cleanWord.split('').entries()) {
        // Add text marker for each letter
        if (addTextMarkers) {
          if (index === cleanWord.length - 1) {
            ref.animations.push(['add-text', ch + ' ']);
          } else {
            ref.animations.push(['add-text', ch]);
          }
        }
        
        // Queue letter animation
        if (alphabets[ch]) {
          alphabets[ch](ref);
          animationsQueued = true;
        } else {
          console.warn(`No animation for character: ${ch}`);
        }
      }
    }
  }
  
  // Start animation if not already running
  if (animationsQueued && ref.animate && ref.pending === false && ref.animations.length > 0) {
    ref.pending = true;
    ref.animate();
  }
  
  return animationsQueued;
};

/**
 * Validate input string contains only allowed characters
 * @param {string} inputString - String to validate
 * @returns {boolean} - True if valid
 */
export const validateInput = (inputString) => {
  const validCharacters = /^[A-Za-z\s.,!?]*$/;
  return validCharacters.test(inputString);
};

/**
 * Get list of available word animations
 * @returns {Array<string>} - Array of available word names
 */
export const getAvailableWords = () => {
  return words.wordList || [];
};

/**
 * Get list of available alphabet animations
 * @returns {Array<string>} - Array of available letters
 */
export const getAvailableAlphabets = () => {
  return 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
};

/**
 * Clear all queued animations
 * @param {Object} ref - Reference object from useThreeScene hook
 */
export const clearAnimations = (ref) => {
  if (ref && ref.animations) {
    ref.animations = [];
    ref.pending = false;
  }
};

/**
 * Get current animation queue status
 * @param {Object} ref - Reference object from useThreeScene hook
 * @returns {Object} - Status information
 */
export const getAnimationStatus = (ref) => {
  if (!ref) {
    return { isRunning: false, queueLength: 0 };
  }
  
  return {
    isRunning: ref.pending || false,
    queueLength: ref.animations ? ref.animations.length : 0,
    hasAvatar: !!ref.avatar
  };
};
