/**
 * Hand Sign Animation Service
 * 
 * Handles communication with the backend for hand sign animations
 * that can be directly applied to the 3D avatar without SiGML parsing.
 */

class HandSignService {
  constructor() {
    this.API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  }

  /**
   * Convert text directly to hand sign animations
   * @param {string} text - Input text to convert
   * @returns {Promise<Object>} - Hand sign animation data
   */
  async textToHandSign(text) {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/text-to-handsign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error converting text to hand signs:', error);
      throw error;
    }
  }

  /**
   * Convert speech audio directly to hand sign animations
   * @param {Blob} audioBlob - Audio data as blob
   * @returns {Promise<Object>} - Hand sign animation data
   */
  async speechToHandSign(audioBlob) {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'audio.wav');

      const response = await fetch(`${this.API_BASE_URL}/api/speech-to-handsign`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error converting speech to hand signs:', error);
      throw error;
    }
  }

  /**
   * Play hand sign animations on the 3D avatar
   * @param {Object} animationData - Animation data from backend
   * @param {Object} threeRef - Three.js scene reference
   * @param {Function} onProgress - Progress callback
   * @returns {Promise<void>}
   */
  async playHandSignAnimations(animationData, threeRef, onProgress = null) {
    if (!threeRef || !threeRef.animations) {
      throw new Error('Invalid Three.js reference provided');
    }

    const { animations, total_duration } = animationData;
    
    // Clear existing animations
    threeRef.animations = [];
    
    // Process each animation in sequence
    for (let i = 0; i < animations.length; i++) {
      const animation = animations[i];
      
      if (onProgress) {
        onProgress({
          current: i + 1,
          total: animations.length,
          gloss: animation.gloss,
          message: `Playing: ${animation.gloss}`
        });
      }

      // Play this animation
      await this._playSingleAnimation(animation, threeRef);
      
      // Add small delay between animations
      if (i < animations.length - 1) {
        await this._delay(100);
      }
    }
  }

  /**
   * Play a single hand sign animation
   * @param {Object} animation - Single animation data
   * @param {Object} threeRef - Three.js scene reference
   * @returns {Promise<void>}
   */
  async _playSingleAnimation(animation, threeRef) {
    const { keyframes, duration } = animation;
    
    if (!keyframes || keyframes.length === 0) {
      console.warn(`No keyframes for animation: ${animation.gloss}`);
      return;
    }

    // Sort keyframes by time
    keyframes.sort((a, b) => a.time - b.time);

    // Apply each keyframe
    for (const keyframe of keyframes) {
      await this._applyKeyframe(keyframe, threeRef);
      
      // Wait until next keyframe time
      if (keyframe.time < duration) {
        await this._delay(duration - keyframe.time);
      }
    }
  }

  /**
   * Apply a single keyframe to the 3D avatar
   * @param {Object} keyframe - Keyframe data
   * @param {Object} threeRef - Three.js scene reference
   * @returns {Promise<void>}
   */
  async _applyKeyframe(keyframe, threeRef) {
    const { transformations } = keyframe;
    
    if (!transformations || !Array.isArray(transformations)) {
      return;
    }

    // Apply each transformation
    for (const transform of transformations) {
      if (!Array.isArray(transform) || transform.length < 5) {
        continue;
      }

      const [boneName, propertyType, axis, value, operation] = transform;
      
      // Find the bone in the Three.js scene
      const bone = this._findBone(threeRef, boneName);
      
      if (bone) {
        this._applyBoneTransform(bone, propertyType, axis, value, operation);
      } else {
        console.warn(`Bone not found: ${boneName}`);
      }
    }

    // Update the scene
    if (threeRef.scene) {
      threeRef.scene.updateMatrixWorld();
    }
  }

  /**
   * Find a bone in the Three.js scene
   * @param {Object} threeRef - Three.js scene reference
   * @param {string} boneName - Name of the bone to find
   * @returns {Object|null} - Bone object or null if not found
   */
  _findBone(threeRef, boneName) {
    if (!threeRef.model) {
      return null;
    }

    // Traverse the model to find the bone
    let bone = null;
    threeRef.model.traverse((child) => {
      if (child.name === boneName) {
        bone = child;
      }
    });

    return bone;
  }

  /**
   * Apply transformation to a bone
   * @param {Object} bone - Three.js bone object
   * @param {string} propertyType - Type of property (rotation, position, scale)
   * @param {string} axis - Axis (x, y, z)
   * @param {string} value - Value to apply
   * @param {string} operation - Operation (+, -, =)
   */
  _applyBoneTransform(bone, propertyType, axis, value, operation) {
    // Parse value (handle Math expressions)
    let parsedValue = this._parseValue(value);
    
    // Get current property
    let property = bone[propertyType];
    if (!property) {
      return;
    }

    // Apply operation
    switch (operation) {
      case '+':
        property[axis] += parsedValue;
        break;
      case '-':
        property[axis] -= parsedValue;
        break;
      case '=':
        property[axis] = parsedValue;
        break;
      default:
        property[axis] = parsedValue;
    }

    // Mark for update
    if (propertyType === 'rotation') {
      bone.updateMatrix();
    }
  }

  /**
   * Parse value string (handle Math expressions)
   * @param {string} value - Value string to parse
   * @returns {number} - Parsed numeric value
   */
  _parseValue(value) {
    if (typeof value === 'number') {
      return value;
    }

    // Handle Math expressions like "Math.PI/2"
    if (value.includes('Math.')) {
      try {
        // Safe evaluation of Math expressions
        return eval(value);
      } catch (e) {
        console.warn(`Invalid Math expression: ${value}`);
        return 0;
      }
    }

    // Parse as float
    const parsed = parseFloat(value);
    return isNaN(parsed) ? 0 : parsed;
  }

  /**
   * Delay utility function
   * @param {number} ms - Milliseconds to delay
   * @returns {Promise<void>}
   */
  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Check if the hand sign service is available
   * @returns {Promise<boolean>} - True if service is available
   */
  async checkService() {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/health`);
      const health = await response.json();
      return health.components?.handsign_generator || false;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }
}

export default new HandSignService();
