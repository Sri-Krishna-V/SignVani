/**
 * Three.js Helper Utilities
 * 
 * This module provides safe accessor functions for Three.js bone manipulation
 * with null safety checks to prevent runtime errors.
 */

/**
 * Safely retrieves a bone from an avatar with null checking
 * 
 * @param {THREE.Object3D} avatar - The avatar model
 * @param {string} boneName - Name of the bone to retrieve
 * @returns {THREE.Object3D|null} The bone object or null if not found
 */
export const safeGetBone = (avatar, boneName) => {
  if (!avatar) {
    console.warn('safeGetBone: avatar is null or undefined');
    return null;
  }

  const bone = avatar.getObjectByName(boneName);
  
  if (!bone) {
    console.warn(`safeGetBone: Bone not found: ${boneName}`);
    return null;
  }

  return bone;
};

/**
 * Safely sets a property on a bone with comprehensive null checking
 * 
 * @param {THREE.Object3D} avatar - The avatar model
 * @param {string} boneName - Name of the bone
 * @param {string} action - Action property (e.g., 'rotation', 'position')
 * @param {string} axis - Axis ('x', 'y', 'z')
 * @param {number} value - Value to set
 * @returns {boolean} True if successful, false otherwise
 */
export const safeSetBoneProperty = (avatar, boneName, action, axis, value) => {
  const bone = safeGetBone(avatar, boneName);
  
  if (!bone) {
    return false;
  }

  if (!bone[action]) {
    console.warn(`safeSetBoneProperty: Action '${action}' not found on bone '${boneName}'`);
    return false;
  }

  if (bone[action][axis] === undefined) {
    console.warn(`safeSetBoneProperty: Axis '${axis}' not found on bone '${boneName}.${action}'`);
    return false;
  }

  bone[action][axis] = value;
  return true;
};

/**
 * Safely gets a property from a bone with comprehensive null checking
 * 
 * @param {THREE.Object3D} avatar - The avatar model
 * @param {string} boneName - Name of the bone
 * @param {string} action - Action property (e.g., 'rotation', 'position')
 * @param {string} axis - Axis ('x', 'y', 'z')
 * @returns {number|null} The property value or null if not found
 */
export const safeGetBoneProperty = (avatar, boneName, action, axis) => {
  const bone = safeGetBone(avatar, boneName);
  
  if (!bone) {
    return null;
  }

  if (!bone[action]) {
    console.warn(`safeGetBoneProperty: Action '${action}' not found on bone '${boneName}'`);
    return null;
  }

  if (bone[action][axis] === undefined) {
    console.warn(`safeGetBoneProperty: Axis '${axis}' not found on bone '${boneName}.${action}'`);
    return null;
  }

  return bone[action][axis];
};

/**
 * Validates that a bone has the required action and axis
 * 
 * @param {THREE.Object3D} bone - The bone object
 * @param {string} action - Action property to validate
 * @param {string} axis - Axis to validate
 * @returns {boolean} True if valid, false otherwise
 */
export const validateBoneAction = (bone, action, axis) => {
  if (!bone) {
    return false;
  }

  if (!bone[action]) {
    return false;
  }

  return bone[action][axis] !== undefined;
};
