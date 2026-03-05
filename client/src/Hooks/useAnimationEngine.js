import { useCallback, useEffect } from 'react';
import { validateBoneAction } from '../Utils/threeHelpers';

/**
 * Custom hook for managing Three.js animation engine
 * Handles animation queue processing and rendering loop
 * 
 * @param {Object} ref - Reference object from useThreeScene hook
 * @param {number} speed - Animation speed (how fast bones move)
 * @param {number} pause - Pause duration between animation frames (ms)
 * @param {Function} onTextUpdate - Optional callback for text updates during animations
 * @returns {Object} Animation control functions
 */
export const useAnimationEngine = (ref, speed, pause, onTextUpdate = null) => {
  
  /**
   * Main animation loop - processes animation queue and renders scene
   * Uses requestAnimationFrame for smooth 60fps rendering
   */
  const animate = useCallback(() => {
    // Stop animation if queue is empty
    if (ref.animations.length === 0) {
      ref.pending = false;
      return;
    }
    
    // Store animation frame ID for proper cleanup
    ref.animationFrameId = requestAnimationFrame(animate);
    
    // Process current animation frame
    if (ref.animations[0].length) {
      if (!ref.flag) {
        // Handle text addition animations
        if (ref.animations[0][0] === 'add-text') {
          if (onTextUpdate) {
            onTextUpdate(ref.animations[0][1]);
          }
          ref.animations.shift();
        } 
        // Handle bone animations
        else {
          for (let i = 0; i < ref.animations[0].length;) {
            const [boneName, action, axis, limit, sign] = ref.animations[0][i];
            
            // Null safety check: ensure avatar and bone exist
            if (!ref.avatar) {
              ref.animations[0].splice(i, 1);
              continue;
            }
            
            const bone = ref.avatar.getObjectByName(boneName);
            if (!bone || !validateBoneAction(bone, action, axis)) {
              // Remove invalid animation and continue
              ref.animations[0].splice(i, 1);
              continue;
            }
            
            // Animate bone towards target limit
            if (sign === "+" && bone[action][axis] < limit) {
              bone[action][axis] += speed;
              bone[action][axis] = Math.min(bone[action][axis], limit);
              i++;
            } 
            else if (sign === "-" && bone[action][axis] > limit) {
              bone[action][axis] -= speed;
              bone[action][axis] = Math.max(bone[action][axis], limit);
              i++;
            } 
            else {
              // Animation complete for this bone
              ref.animations[0].splice(i, 1);
            }
          }
        }
      }
    } 
    // Frame complete, add pause before next frame
    else {
      ref.flag = true;
      setTimeout(() => {
        ref.flag = false;
      }, pause);
      ref.animations.shift();
    }
    
    // Render scene with null safety check
    if (ref.renderer && ref.scene && ref.camera) {
      ref.renderer.render(ref.scene, ref.camera);
    }
  }, [ref, speed, pause, onTextUpdate]);
  
  // Assign animate function to ref so it can be called externally
  useEffect(() => {
    ref.animate = animate;
  }, [ref, animate]);
  
  /**
   * Start the animation loop if not already running
   */
  const startAnimation = useCallback(() => {
    if (ref.animations.length > 0 && !ref.pending) {
      ref.pending = true;
      ref.animate();
    }
  }, [ref]);
  
  /**
   * Stop the current animation loop
   */
  const stopAnimation = useCallback(() => {
    if (ref.animationFrameId) {
      cancelAnimationFrame(ref.animationFrameId);
      ref.animationFrameId = null;
      ref.pending = false;
    }
  }, [ref]);
  
  /**
   * Clear all queued animations
   */
  const clearAnimations = useCallback(() => {
    ref.animations = [];
    ref.pending = false;
  }, [ref]);
  
  /**
   * Get current animation queue status
   * @returns {Object} Status information
   */
  const getStatus = useCallback(() => {
    return {
      isAnimating: ref.pending,
      queueLength: ref.animations.length,
      currentFrameLength: ref.animations[0]?.length || 0
    };
  }, [ref]);
  
  return {
    startAnimation,
    stopAnimation,
    clearAnimations,
    getStatus
  };
};
