import wordsData from '../Data/wordsData.json';

/**
 * Safely evaluates Math expressions from JSON strings
 * Only allows Math.PI operations for security
 */
const evaluateExpression = (expr) => {
  if (typeof expr !== 'string') return expr;
  
  // Security: Only allow Math.PI expressions
  if (expr.includes('Math.PI')) {
    try {
      // eslint-disable-next-line no-eval
      return eval(expr);
    } catch (e) {
      console.error(`Failed to evaluate expression: ${expr}`, e);
      return 0;
    }
  }
  
  // Return numeric values as-is
  return parseFloat(expr) || 0;
};

/**
 * Loads a single word animation from JSON data
 * @param {string} wordName - The word to load (e.g., 'TIME', 'HOME')
 * @returns {Function} Animation function that takes a ref parameter
 */
export const loadWordAnimation = (wordName) => {
  const wordData = wordsData[wordName.toUpperCase()];
  
  if (!wordData) {
    console.warn(`Word "${wordName}" not found in wordsData.json`);
    return null;
  }
  
  // Return a function that matches the existing word animation signature
  return (ref) => {
    const animations = [];
    
    // Process each keyframe
    wordData.keyframes.forEach(keyframe => {
      const frameAnimations = [];
      
      // Process each transformation in the keyframe
      keyframe.transformations.forEach(transformation => {
        const [boneName, type, axis, value, direction] = transformation;
        
        // Evaluate the Math.PI expression if present
        const evaluatedValue = evaluateExpression(value);
        
        // Add to frame animations with the same format as original code
        frameAnimations.push([boneName, type, axis, evaluatedValue, direction]);
      });
      
      animations.push(frameAnimations);
    });
    
    // Push all animations to ref and trigger animation
    animations.forEach(animation => {
      ref.animations.push(animation);
    });
    
    if (!ref.pending) {
      ref.pending = true;
      ref.animate();
    }
  };
};

/**
 * Gets list of all available words from JSON
 * @returns {Array<string>} Array of word names
 */
export const getAvailableWordsFromJSON = () => {
  return Object.keys(wordsData);
};

/**
 * Loads all word animations from JSON
 * @returns {Object} Object with word names as keys and animation functions as values
 */
export const loadAllWords = () => {
  const words = {};
  
  Object.keys(wordsData).forEach(wordName => {
    words[wordName] = loadWordAnimation(wordName);
  });
  
  return words;
};

/**
 * Get description for a specific word
 * @param {string} wordName - The word name
 * @returns {string} Description of the sign
 */
export const getWordDescription = (wordName) => {
  const wordData = wordsData[wordName.toUpperCase()];
  return wordData ? wordData.description : '';
};

export default {
  loadWordAnimation,
  getAvailableWordsFromJSON,
  loadAllWords,
  getWordDescription
};
