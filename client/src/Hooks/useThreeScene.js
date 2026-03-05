import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { defaultPose } from '../Animations/defaultPose';
import { disposeThreeResources } from '../Utils/threeCleanup';

/**
 * Custom hook for setting up and managing a Three.js scene with avatar
 * Eliminates code duplication across Convert, LearnSign, and Video pages
 * 
 * @param {string} bot - Path to the GLTF model file
 * @param {string} canvasId - ID of the canvas element to attach renderer to
 * @param {Object} options - Optional configuration options
 * @param {number} options.cameraFov - Camera field of view (default: 30)
 * @param {number} options.cameraZ - Camera Z position (default: 1.6)
 * @param {number} options.cameraY - Camera Y position (default: 1.4)
 * @param {number} options.aspectRatioWidth - Width multiplier for aspect ratio (default: 0.57)
 * @param {number} options.backgroundColor - Scene background color (default: 0xdddddd)
 * @param {number} options.lightIntensity - Spotlight intensity (default: 2)
 * @param {boolean} options.antialias - Enable antialiasing (default: false for Pi performance)
 * @param {number} options.pixelRatio - Pixel ratio (default: 1 for Pi performance)
 * @returns {Object} ref - Reference object containing scene, renderer, camera, avatar, and animation state
 */
export const useThreeScene = (bot, canvasId = 'canvas', options = {}) => {
  const componentRef = useRef({});
  const { current: ref } = componentRef;
  
  const {
    cameraFov = 30,
    cameraZ = 1.6,
    cameraY = 1.4,
    aspectRatioWidth = 0.57,
    backgroundColor = 0xdddddd,
    lightIntensity = 2,
    antialias = false, // Disabled for Raspberry Pi performance
    pixelRatio = 1 // Force 1:1 pixel ratio for better Pi performance
  } = options;
  
  useEffect(() => {
    // Initialize state refs
    ref.flag = false;
    ref.pending = false;
    ref.animations = [];
    ref.characters = [];
    
    // Create scene
    ref.scene = new THREE.Scene();
    ref.scene.background = new THREE.Color(backgroundColor);
    
    // Add lighting
    const spotLight = new THREE.SpotLight(0xffffff, lightIntensity);
    spotLight.position.set(0, 5, 5);
    ref.scene.add(spotLight);
    
    // Create camera with configurable aspect ratio
    const aspectRatio = window.innerWidth * aspectRatioWidth / (window.innerHeight - 70);
    ref.camera = new THREE.PerspectiveCamera(cameraFov, aspectRatio, 0.1, 1000);
    ref.camera.position.z = cameraZ;
    ref.camera.position.y = cameraY;
    
    // Create renderer with Raspberry Pi optimizations
    ref.renderer = new THREE.WebGLRenderer({ 
      antialias,
      powerPreference: 'low-power',  // Critical for Raspberry Pi
      precision: 'mediump'  // Use medium precision for better performance
    });
    
    ref.renderer.setPixelRatio(pixelRatio);
    ref.renderer.setSize(window.innerWidth * aspectRatioWidth, window.innerHeight - 70);
    
    // Attach renderer to DOM
    const canvasElement = document.getElementById(canvasId);
    if (canvasElement) {
      canvasElement.innerHTML = "";
      canvasElement.appendChild(ref.renderer.domElement);
    } else {
      console.error(`Canvas element with id "${canvasId}" not found`);
      return;
    }
    
    // Load 3D model
    const loader = new GLTFLoader();
    loader.load(
      bot,
      (gltf) => {
        // Optimize model for Raspberry Pi performance
        gltf.scene.traverse((child) => {
          if (child.type === 'SkinnedMesh') {
            child.frustumCulled = false;
            // Disable shadows for better Raspberry Pi performance
            child.castShadow = false;
            child.receiveShadow = false;
          }
        });
        
        ref.avatar = gltf.scene;
        ref.scene.add(ref.avatar);
        defaultPose(ref);
      },
      (xhr) => {
        const progress = Math.round((xhr.loaded / xhr.total) * 100);
        console.log(`Model loading: ${progress}%`);
      },
      (error) => {
        console.error('Error loading model:', error);
      }
    );
    
    // Cleanup function to prevent memory leaks
    return () => {
      disposeThreeResources(ref);
    };
  }, [bot, canvasId, cameraFov, cameraZ, cameraY, aspectRatioWidth, backgroundColor, lightIntensity, antialias, pixelRatio, ref]);
  
  return ref;
};
