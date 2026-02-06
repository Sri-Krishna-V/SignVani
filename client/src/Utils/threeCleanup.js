/**
 * Three.js Resource Cleanup Utility
 * 
 * This module provides utilities for properly disposing of Three.js resources
 * to prevent memory leaks, especially critical on resource-constrained devices
 * like Raspberry Pi.
 */

/**
 * Disposes all Three.js resources associated with a component ref
 * 
 * @param {Object} ref - Component ref containing Three.js objects
 * @param {number} ref.animationFrameId - Animation frame request ID
 * @param {THREE.WebGLRenderer} ref.renderer - WebGL renderer instance
 * @param {THREE.Scene} ref.scene - Scene instance
 * @param {THREE.Object3D} ref.avatar - Avatar model instance
 * @param {Array} ref.animations - Animation queue
 */
export const disposeThreeResources = (ref) => {
  if (!ref) {
    console.warn('disposeThreeResources called with null/undefined ref');
    return;
  }

  // Cancel any pending animation frames
  if (ref.animationFrameId) {
    cancelAnimationFrame(ref.animationFrameId);
    ref.animationFrameId = null;
  }

  // Dispose scene and all its children
  if (ref.scene) {
    ref.scene.traverse((object) => {
      // Dispose geometries
      if (object.geometry) {
        object.geometry.dispose();
      }

      // Dispose materials
      if (object.material) {
        if (Array.isArray(object.material)) {
          object.material.forEach(material => {
            disposeMaterial(material);
          });
        } else {
          disposeMaterial(object.material);
        }
      }

      // Dispose textures
      if (object.texture) {
        object.texture.dispose();
      }
    });

    ref.scene.clear();
    ref.scene = null;
  }

  // Dispose renderer
  if (ref.renderer) {
    ref.renderer.dispose();
    ref.renderer.forceContextLoss();
    
    // Remove DOM element
    if (ref.renderer.domElement && ref.renderer.domElement.parentNode) {
      ref.renderer.domElement.parentNode.removeChild(ref.renderer.domElement);
    }
    
    ref.renderer.domElement = null;
    ref.renderer = null;
  }

  // Clear avatar reference
  if (ref.avatar) {
    ref.avatar = null;
  }

  // Clear camera reference
  if (ref.camera) {
    ref.camera = null;
  }

  // Clear animations array
  if (ref.animations) {
    ref.animations = [];
  }

  // Clear characters array
  if (ref.characters) {
    ref.characters = [];
  }

  // Reset flags
  ref.flag = false;
  ref.pending = false;
};

/**
 * Helper function to properly dispose of a material and its textures
 * 
 * @param {THREE.Material} material - Material to dispose
 */
const disposeMaterial = (material) => {
  if (!material) return;

  // Dispose all texture maps
  const textureProperties = [
    'map',
    'lightMap',
    'bumpMap',
    'normalMap',
    'specularMap',
    'envMap',
    'alphaMap',
    'aoMap',
    'displacementMap',
    'emissiveMap',
    'gradientMap',
    'metalnessMap',
    'roughnessMap'
  ];

  textureProperties.forEach(property => {
    if (material[property] && material[property].dispose) {
      material[property].dispose();
    }
  });

  material.dispose();
};
