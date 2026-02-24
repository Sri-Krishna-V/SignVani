/**
 * Enhanced Animation Player for SignVani
 * Handles both traditional animations and backend-generated HamNoSys codes
 */

import * as alphabets from '../Animations/alphabets';
import * as words from '../Animations/words';
import { getWordAnimation } from '../Animations/words';
import apiService from './apiService';

// Comprehensive bidirectional reset frame — mirrors animationPlayer.js DEFAULT_POSE_FRAME.
// Each bone-axis pair appears twice ('+' and '-') so the avatar can reach the default
// position regardless of which direction the preceding animation left the bone.
const DEFAULT_POSE_FRAME = [
  ["mixamorigNeck",         "rotation", "x",  Math.PI / 12,   "+"],
  ["mixamorigNeck",         "rotation", "x",  Math.PI / 12,   "-"],
  ["mixamorigLeftArm",      "rotation", "z", -Math.PI / 3,    "+"],
  ["mixamorigLeftArm",      "rotation", "z", -Math.PI / 3,    "-"],
  ["mixamorigLeftForeArm",  "rotation", "y", -Math.PI / 1.5,  "+"],
  ["mixamorigLeftForeArm",  "rotation", "y", -Math.PI / 1.5,  "-"],
  ["mixamorigRightArm",     "rotation", "z",  Math.PI / 3,    "+"],
  ["mixamorigRightArm",     "rotation", "z",  Math.PI / 3,    "-"],
  ["mixamorigRightForeArm", "rotation", "y",  Math.PI / 1.5,  "+"],
  ["mixamorigRightForeArm", "rotation", "y",  Math.PI / 1.5,  "-"],
  ["mixamorigLeftArm",      "rotation", "x", 0, "+"], ["mixamorigLeftArm",      "rotation", "x", 0, "-"],
  ["mixamorigLeftArm",      "rotation", "y", 0, "+"], ["mixamorigLeftArm",      "rotation", "y", 0, "-"],
  ["mixamorigRightArm",     "rotation", "x", 0, "+"], ["mixamorigRightArm",     "rotation", "x", 0, "-"],
  ["mixamorigRightArm",     "rotation", "y", 0, "+"], ["mixamorigRightArm",     "rotation", "y", 0, "-"],
  ["mixamorigLeftForeArm",  "rotation", "x", 0, "+"], ["mixamorigLeftForeArm",  "rotation", "x", 0, "-"],
  ["mixamorigLeftForeArm",  "rotation", "z", 0, "+"], ["mixamorigLeftForeArm",  "rotation", "z", 0, "-"],
  ["mixamorigRightForeArm", "rotation", "x", 0, "+"], ["mixamorigRightForeArm", "rotation", "x", 0, "-"],
  ["mixamorigRightForeArm", "rotation", "z", 0, "+"], ["mixamorigRightForeArm", "rotation", "z", 0, "-"],
  ["mixamorigLeftHand",     "rotation", "x", 0, "+"], ["mixamorigLeftHand",     "rotation", "x", 0, "-"],
  ["mixamorigLeftHand",     "rotation", "y", 0, "+"], ["mixamorigLeftHand",     "rotation", "y", 0, "-"],
  ["mixamorigLeftHand",     "rotation", "z", 0, "+"], ["mixamorigLeftHand",     "rotation", "z", 0, "-"],
  ["mixamorigRightHand",    "rotation", "x", 0, "+"], ["mixamorigRightHand",    "rotation", "x", 0, "-"],
  ["mixamorigRightHand",    "rotation", "y", 0, "+"], ["mixamorigRightHand",    "rotation", "y", 0, "-"],
  ["mixamorigRightHand",    "rotation", "z", 0, "+"], ["mixamorigRightHand",    "rotation", "z", 0, "-"],
  ["mixamorigNeck",         "rotation", "y", 0, "+"], ["mixamorigNeck",         "rotation", "y", 0, "-"],
  ["mixamorigNeck",         "rotation", "z", 0, "+"], ["mixamorigNeck",         "rotation", "z", 0, "-"],
];

class EnhancedAnimationPlayer {
  constructor(ref) {
    this.ref = ref;
    this.backendMode = false;
    this.currentGloss = '';
    this.currentHamNoSys = [];
    this.currentSiGML = '';
  }

  /**
   * Play text using backend processing
   * @param {string} text - Input text to process
   * @param {Function} onProgress - Progress callback
   * @returns {Promise<Object>} - Processing result
   */
  async playTextWithBackend(text, onProgress = null) {
    try {
      if (onProgress) onProgress({ stage: 'processing', message: 'Sending text to backend...' });

      // Send text to backend for processing
      const result = await apiService.textToSign(text);
      
      if (onProgress) onProgress({ stage: 'processing', message: 'Processing complete!' });

      // Store results
      this.currentGloss = result.gloss;
      this.currentHamNoSys = result.hamnosys || [];
      this.currentSiGML = result.sigml;

      // Animate using the ISL gloss (SOV word order) from the backend.
      // Fall back to the original text only if the backend returned no glosses.
      const glossText = (result.glosses && result.glosses.length > 0)
        ? result.glosses.join(' ')
        : text;
      await this._playTraditionalAnimation(glossText);

      return result;

    } catch (error) {
      console.error('Backend processing failed:', error);
      // Fallback to traditional animation
      await this._playTraditionalAnimation(text);
      throw error;
    }
  }

  /**
   * Process speech audio with backend
   * @param {Blob} audioBlob - Audio data
   * @param {Function} onProgress - Progress callback
   * @returns {Promise<Object>} - Processing result
   */
  async playSpeechWithBackend(audioBlob, onProgress = null) {
    try {
      if (onProgress) onProgress({ stage: 'transcribing', message: 'Transcribing audio...' });

      // Send audio to backend
      const result = await apiService.speechToSign(audioBlob);
      
      if (onProgress) onProgress({ stage: 'processing', message: 'Converting to sign language...' });

      // Store results
      this.currentGloss = result.gloss;
      this.currentHamNoSys = result.hamnosys || [];
      this.currentSiGML = result.sigml;

      if (onProgress) onProgress({ stage: 'complete', message: 'Ready to play!' });

      // Animate using the ISL gloss (SOV word order) from the backend.
      // Fall back to the original transcript only if no glosses were returned.
      const glossText = (result.glosses && result.glosses.length > 0)
        ? result.glosses.join(' ')
        : result.original_text;
      await this._playTraditionalAnimation(glossText);

      return result;

    } catch (error) {
      console.error('Speech processing failed:', error);
      throw error;
    }
  }

  /**
   * Play traditional animation (fallback)
   * @param {string} text - Text to animate
   * @private
   */
  async _playTraditionalAnimation(text) {
    if (!this.ref || !this.ref.animations) {
      throw new Error('Invalid animation reference');
    }

    // Validate input
    if (!text || typeof text !== 'string') {
      throw new Error('Invalid text for animation');
    }

    // Sanitize and limit length
    const sanitized = text.trim().slice(0, 500);
    if (sanitized.length === 0) {
      throw new Error('Please enter some text to animate');
    }

    // Validate characters - allow letters, spaces, and basic punctuation
    if (!/^[A-Za-z\s.,!?]*$/.test(sanitized)) {
      throw new Error('Only letters (A-Z), spaces, and basic punctuation (. , ! ?) are allowed');
    }

    const wordArray = sanitized.toUpperCase().split(' ');
    let animationsQueued = false;

    // Clear existing animations
    this.ref.animations = [];

    for (const word of wordArray) {
      if (word.length === 0) continue;

      // Strip punctuation so "HELLO." matches "HELLO" in wordsData.json
      const cleanWord = word.replace(/[^A-Z]/g, '');
      if (cleanWord.length === 0) continue;

      // Try word animation first — preserve special chars (e.g. PLEASE_NAMASTE) before stripping
      const wordAnim = words[word] || getWordAnimation(word)
                    || words[cleanWord] || getWordAnimation(cleanWord);
      if (wordAnim) {
        this.ref.animations.push(['add-text', cleanWord + ' ']);
        wordAnim(this.ref);
        animationsQueued = true;
      } else {
        // Fall back to letter-by-letter fingerspelling
        for (const [index, ch] of cleanWord.split('').entries()) {
          if (index === cleanWord.length - 1) {
            this.ref.animations.push(['add-text', ch + ' ']);
          } else {
            this.ref.animations.push(['add-text', ch]);
          }

          if (alphabets[ch]) {
            alphabets[ch](this.ref);
            animationsQueued = true;
          }
        }
      }
    }

    // Start animation
    if (animationsQueued && this.ref.animate && this.ref.pending === false) {
      this.ref.pending = true;
      this.ref.animate();
    }

    // Append reset-to-default-pose as the final queued frame
    if (animationsQueued) {
      this.ref.animations.push([...DEFAULT_POSE_FRAME]);
    }

    return animationsQueued;
  }

  /**
   * Get current processing results
   * @returns {Object} - Current gloss, HamNoSys, and SiGML data
   */
  getCurrentResults() {
    return {
      gloss: this.currentGloss,
      hamnosys: this.currentHamNoSys,
      sigml: this.currentSiGML,
      hasBackendData: this.currentGloss.length > 0
    };
  }

  /**
   * Clear current results
   */
  clearResults() {
    this.currentGloss = '';
    this.currentHamNoSys = [];
    this.currentSiGML = '';
  }

  /**
   * Enable/disable backend mode
   * @param {boolean} enabled - Whether to use backend processing
   */
  setBackendMode(enabled) {
    this.backendMode = enabled;
  }

  /**
   * Check if backend mode is enabled
   * @returns {boolean} - Backend mode status
   */
  isBackendMode() {
    return this.backendMode;
  }
}

/**
 * Create enhanced animation player instance
 * @param {Object} ref - Three.js scene reference
 * @returns {EnhancedAnimationPlayer} - Animation player instance
 */
export const createEnhancedPlayer = (ref) => {
  return new EnhancedAnimationPlayer(ref);
};

/**
 * Legacy compatibility functions
 */
export const playString = async (ref, inputString, addTextMarkers = true) => {
  const player = createEnhancedPlayer(ref);
  return await player._playTraditionalAnimation(inputString);
};

export const playAnimation = (ref, character) => {
  const upperChar = character.toUpperCase();
  
  if (!ref || !ref.animations) {
    console.error('Invalid ref object provided to playAnimation');
    return false;
  }
  
  if (upperChar.length !== 1 || !/[A-Z]/.test(upperChar)) {
    console.warn(`Invalid character for animation: ${character}`);
    return false;
  }
  
  if (!alphabets[upperChar]) {
    console.warn(`No animation found for character: ${upperChar}`);
    return false;
  }
  
  alphabets[upperChar](ref);

  // Return to neutral pose after the sign
  ref.animations.push([...DEFAULT_POSE_FRAME]);

  if (ref.animate && ref.pending === false && ref.animations.length > 0) {
    ref.pending = true;
    ref.animate();
  }
  
  return true;
};

export const playWord = (ref, word) => {
  const upperWord = word.toUpperCase();
  const cleanWord = upperWord.replace(/[^A-Z]/g, '');
  
  if (!ref || !ref.animations) {
    console.error('Invalid ref object provided to playWord');
    return false;
  }
  
  // Try original word name (preserving underscores) before stripping
  const wordAnim = words[upperWord] || getWordAnimation(upperWord)
                || words[cleanWord] || getWordAnimation(cleanWord);
  if (!wordAnim) {
    console.warn(`No animation found for word: ${cleanWord}`);
    return false;
  }
  
  wordAnim(ref);

  // Return to neutral pose after the sign
  ref.animations.push([...DEFAULT_POSE_FRAME]);

  if (ref.animate && ref.pending === false && ref.animations.length > 0) {
    ref.pending = true;
    ref.animate();
  }
  
  return true;
};

export default EnhancedAnimationPlayer;
