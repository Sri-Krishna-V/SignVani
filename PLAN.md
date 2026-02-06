# Plan: Improve Sign-Kit Codebase Quality & Maintainability

The Sign-Kit project has **45 improvement opportunities** across critical bugs (memory leaks, null safety), massive code duplication (96% similarity between Three.js pages, 2600+ lines in alphabet files), security gaps, accessibility issues, and outdated dependencies. Prioritizing fixes will significantly enhance stability, performance, and maintainability.

**Target Platform:** Raspberry Pi 4B (1.5GHz quad-core ARM Cortex-A72, 2-8GB RAM, VideoCore VI GPU)

**Performance Constraints:**
- Limited GPU resources compared to desktop
- Memory constraints (optimize for 2GB RAM minimum)
- ARM architecture considerations
- Lower WebGL performance capabilities

---

## Phase 1: Fix Critical Memory Leaks and Crashes

### 1.1 Add Three.js Resource Cleanup (Priority: CRITICAL)

**Problem:** Three.js scenes, renderers, geometries, and materials persist in memory after component unmount, causing memory leaks especially on resource-constrained Raspberry Pi.

**Files to modify:**
- `client/src/Pages/Convert.js`
- `client/src/Pages/LearnSign.js`
- `client/src/Pages/Video.js`

**Implementation Steps:**

#### 1.1.1 Create Cleanup Utility Function
Create `client/src/Utils/threeCleanup.js`:
```javascript
export const disposeThreeResources = (ref) => {
  // Cancel any pending animation frames
  if (ref.animationFrameId) {
    cancelAnimationFrame(ref.animationFrameId);
  }
  
  // Dispose renderer
  if (ref.renderer) {
    ref.renderer.dispose();
    ref.renderer.forceContextLoss();
    ref.renderer.domElement = null;
    ref.renderer = null;
  }
  
  // Dispose scene and all its children
  if (ref.scene) {
    ref.scene.traverse((object) => {
      if (object.geometry) {
        object.geometry.dispose();
      }
      if (object.material) {
        if (Array.isArray(object.material)) {
          object.material.forEach(material => material.dispose());
        } else {
          object.material.dispose();
        }
      }
      if (object.texture) {
        object.texture.dispose();
      }
    });
    ref.scene.clear();
    ref.scene = null;
  }
  
  // Clear avatar reference
  if (ref.avatar) {
    ref.avatar = null;
  }
  
  // Clear animations array
  if (ref.animations) {
    ref.animations = [];
  }
};
```

#### 1.1.2 Add Cleanup to useEffect in Convert.js
In `client/src/Pages/Convert.js`, modify the useEffect hook:
```javascript
useEffect(() => {
  // ... existing initialization code ...
  
  // Cleanup function
  return () => {
    disposeThreeResources(ref);
  };
}, [ref, bot]);
```

#### 1.1.3 Add Cleanup to LearnSign.js and Video.js
Repeat the same cleanup pattern in:
- `client/src/Pages/LearnSign.js` (line ~30, in useEffect)
- `client/src/Pages/Video.js` (line ~40, in useEffect)

#### 1.1.4 Optimize Animation Frame Management
In the `animate()` function, store the animation frame ID:
```javascript
ref.animate = () => {
  if(ref.animations.length === 0){
    ref.pending = false;
    return;
  }
  ref.animationFrameId = requestAnimationFrame(ref.animate);
  // ... rest of animation logic ...
};
```

**Raspberry Pi Optimization:**
- Reduces memory pressure on limited RAM
- Prevents GPU context issues
- Improves tab switching performance

---

### 1.2 Add Null Safety Checks (Priority: CRITICAL)

**Problem:** `getObjectByName()` can return `null` if bone names don't exist, causing crashes in animation loop.

**Files to modify:**
- `client/src/Pages/Convert.js` (lines 104-116)
- `client/src/Pages/LearnSign.js` (lines 87-99)
- `client/src/Pages/Video.js` (lines 108-120)

**Implementation Steps:**

#### 1.2.1 Create Safe Bone Accessor Function
Add to `client/src/Utils/threeHelpers.js`:
```javascript
export const safeGetBone = (avatar, boneName, action, axis) => {
  if (!avatar) return null;
  
  const bone = avatar.getObjectByName(boneName);
  if (!bone) {
    console.warn(`Bone not found: ${boneName}`);
    return null;
  }
  
  if (!bone[action]) {
    console.warn(`Action not found on bone ${boneName}: ${action}`);
    return null;
  }
  
  return bone;
};

export const safeSetBoneProperty = (avatar, boneName, action, axis, value) => {
  const bone = safeGetBone(avatar, boneName, action, axis);
  if (bone && bone[action]) {
    bone[action][axis] = value;
    return true;
  }
  return false;
};
```

#### 1.2.2 Update Animation Logic with Null Checks
Replace animation loop in all three files:
```javascript
// OLD CODE (unsafe):
if(sign === "+" && ref.avatar.getObjectByName(boneName)[action][axis] < limit){
  ref.avatar.getObjectByName(boneName)[action][axis] += speed;
  // ...
}

// NEW CODE (safe):
const bone = ref.avatar.getObjectByName(boneName);
if (!bone || !bone[action]) {
  ref.animations[0].splice(i, 1);
  continue;
}

if(sign === "+" && bone[action][axis] < limit){
  bone[action][axis] += speed;
  bone[action][axis] = Math.min(bone[action][axis], limit);
  i++;
}
else if(sign === "-" && bone[action][axis] > limit){
  bone[action][axis] -= speed;
  bone[action][axis] = Math.max(bone[action][axis], limit);
  i++;
}
else{
  ref.animations[0].splice(i, 1);
}
```

**Raspberry Pi Optimization:**
- Prevents crashes that require page reload
- Reduces debugging overhead on slower hardware

---

## Phase 2: Eliminate Code Duplication

### 2.1 Create Custom Hooks for Three.js Setup (Priority: HIGH)

**Problem:** 96% code duplication across Convert.js, LearnSign.js, and Video.js. Each file duplicates ~200 lines of Three.js initialization.

**Files to create:**
- `client/src/Hooks/useThreeScene.js`
- `client/src/Hooks/useAnimationEngine.js`

#### 2.1.1 Create useThreeScene Hook
Create `client/src/Hooks/useThreeScene.js`:
```javascript
import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
import { defaultPose } from '../Animations/defaultPose';
import { disposeThreeResources } from '../Utils/threeCleanup';

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
    antialias = false, // Disable for Raspberry Pi performance
    pixelRatio = 1 // Force 1:1 pixel ratio for better Pi performance
  } = options;
  
  useEffect(() => {
    // Initialize refs
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
    
    // Create camera
    const aspectRatio = window.innerWidth * aspectRatioWidth / (window.innerHeight - 70);
    ref.camera = new THREE.PerspectiveCamera(cameraFov, aspectRatio, 0.1, 1000);
    ref.camera.position.z = cameraZ;
    ref.camera.position.y = cameraY;
    
    // Create renderer with Raspberry Pi optimizations
    ref.renderer = new THREE.WebGLRenderer({ 
      antialias,
      powerPreference: 'low-power', // Important for Raspberry Pi
      precision: 'mediump' // Use medium precision for better performance
    });
    
    ref.renderer.setPixelRatio(pixelRatio);
    ref.renderer.setSize(
      window.innerWidth * aspectRatioWidth, 
      window.innerHeight - 70
    );
    
    // Mount to DOM
    const canvasElement = document.getElementById(canvasId);
    if (canvasElement) {
      canvasElement.innerHTML = '';
      canvasElement.appendChild(ref.renderer.domElement);
    }
    
    // Load model
    const loader = new GLTFLoader();
    ref.isModelLoaded = false;
    
    loader.load(
      bot,
      (gltf) => {
        gltf.scene.traverse((child) => {
          if (child.type === 'SkinnedMesh') {
            child.frustumCulled = false;
            // Reduce shadow complexity for Raspberry Pi
            child.castShadow = false;
            child.receiveShadow = false;
          }
        });
        ref.avatar = gltf.scene;
        ref.scene.add(ref.avatar);
        defaultPose(ref);
        ref.isModelLoaded = true;
      },
      (xhr) => {
        const percentComplete = (xhr.loaded / xhr.total) * 100;
        console.log(`Model loading: ${Math.round(percentComplete)}%`);
      },
      (error) => {
        console.error('Error loading model:', error);
      }
    );
    
    // Cleanup on unmount
    return () => {
      disposeThreeResources(ref);
    };
  }, [bot]);
  
  return ref;
};
```

#### 2.1.2 Create useAnimationEngine Hook
Create `client/src/Hooks/useAnimationEngine.js`:
```javascript
import { useCallback } from 'react';

export const useAnimationEngine = (ref, speed, pause) => {
  const animate = useCallback(() => {
    if (ref.animations.length === 0) {
      ref.pending = false;
      return;
    }
    
    ref.animationFrameId = requestAnimationFrame(ref.animate);
    
    if (ref.animations[0].length) {
      if (!ref.flag) {
        for (let i = 0; i < ref.animations[0].length;) {
          const [boneName, action, axis, limit, sign] = ref.animations[0][i];
          
          // Null safety check
          const bone = ref.avatar?.getObjectByName(boneName);
          if (!bone || !bone[action]) {
            ref.animations[0].splice(i, 1);
            continue;
          }
          
          // Animate bone
          if (sign === '+' && bone[action][axis] < limit) {
            bone[action][axis] += speed;
            bone[action][axis] = Math.min(bone[action][axis], limit);
            i++;
          } else if (sign === '-' && bone[action][axis] > limit) {
            bone[action][axis] -= speed;
            bone[action][axis] = Math.max(bone[action][axis], limit);
            i++;
          } else {
            ref.animations[0].splice(i, 1);
          }
        }
      }
    } else {
      ref.flag = true;
      setTimeout(() => {
        ref.flag = false;
      }, pause);
      ref.animations.shift();
    }
    
    if (ref.renderer && ref.scene && ref.camera) {
      ref.renderer.render(ref.scene, ref.camera);
    }
  }, [ref, speed, pause]);
  
  ref.animate = animate;
  
  return {
    startAnimation: () => {
      if (ref.pending === false) {
        ref.pending = true;
        ref.animate();
      }
    },
    stopAnimation: () => {
      if (ref.animationFrameId) {
        cancelAnimationFrame(ref.animationFrameId);
      }
      ref.pending = false;
    },
    clearAnimations: () => {
      ref.animations = [];
      ref.pending = false;
    }
  };
};
```

#### 2.1.3 Refactor Pages to Use Hooks
Update `client/src/Pages/Convert.js`:
```javascript
import { useThreeScene } from '../Hooks/useThreeScene';
import { useAnimationEngine } from '../Hooks/useAnimationEngine';

function Convert() {
  // ... existing state declarations ...
  
  // Replace all Three.js setup code with:
  const ref = useThreeScene(bot, 'canvas', {
    antialias: false, // Disabled for Raspberry Pi
    pixelRatio: 1
  });
  
  const { startAnimation, stopAnimation, clearAnimations } = useAnimationEngine(ref, speed, pause);
  
  // ... rest of component logic ...
}
```

Repeat for `LearnSign.js` and `Video.js`.

**Benefits:**
- Reduces bundle size by ~400 lines
- Consistent behavior across pages
- Single point of optimization for Raspberry Pi
- Easier to maintain and test

---

### 2.2 Refactor Alphabet Animations to JSON Data (Priority: HIGH)

**Problem:** 26 alphabet files contain 2,600+ lines of repetitive code. Each file is a function that generates animation arrays.

**Files to create:**
- `client/src/Animations/Data/alphabetAnimations.json`
- `client/src/Animations/animationPlayer.js`

#### 2.2.1 Create JSON Animation Data Structure
Create `client/src/Animations/Data/alphabetAnimations.json`:
```json
{
  "A": [
    {
      "bones": [
        ["mixamorigLeftHandIndex1", "rotation", "y", -0.349, "-"],
        ["mixamorigLeftHandMiddle1", "rotation", "y", -0.174, "-"],
        ["mixamorigLeftHandRing1", "rotation", "y", 0.174, "+"],
        ["mixamorigLeftHandPinky1", "rotation", "y", 0.349, "+"],
        ["mixamorigLeftHand", "rotation", "x", 1.571, "+"],
        ["mixamorigLeftHand", "rotation", "z", 0.524, "+"],
        ["mixamorigLeftHand", "rotation", "y", 0.349, "+"],
        ["mixamorigLeftForeArm", "rotation", "x", 0.314, "+"],
        ["mixamorigLeftForeArm", "rotation", "z", -0.174, "-"],
        ["mixamorigLeftArm", "rotation", "x", -0.285, "-"],
        ["mixamorigRightHandMiddle1", "rotation", "z", 1.571, "+"],
        ["mixamorigRightHandMiddle2", "rotation", "z", 1.571, "+"],
        ["mixamorigRightHandMiddle3", "rotation", "z", 1.571, "+"]
        // ... continue for all bones in A animation
      ]
    },
    {
      "bones": [
        // Reset animations back to 0
        ["mixamorigLeftHandIndex1", "rotation", "y", 0, "+"],
        ["mixamorigLeftHandMiddle1", "rotation", "y", 0, "+"]
        // ... reset all bones
      ]
    }
  ],
  "B": [
    // ... B animation data ...
  ]
  // ... continue for all 26 letters
}
```

#### 2.2.2 Create Animation Player
Create `client/src/Animations/animationPlayer.js`:
```javascript
import animationData from './Data/alphabetAnimations.json';
import * as words from './words';

// Cache for lazy-loaded animations
const animationCache = new Map();

export const playAnimation = (ref, character) => {
  const upperChar = character.toUpperCase();
  
  // Check if it's a word animation
  if (words[upperChar]) {
    words[upperChar](ref);
    return true;
  }
  
  // Check if it's a letter
  const animations = animationData[upperChar];
  if (!animations) {
    console.warn(`No animation found for character: ${character}`);
    return false;
  }
  
  // Add animation frames to queue
  animations.forEach(frame => {
    ref.animations.push(frame.bones);
  });
  
  // Start animation if not already running
  if (ref.pending === false) {
    ref.pending = true;
    ref.animate();
  }
  
  return true;
};

export const playString = (ref, inputString) => {
  const words = inputString.toUpperCase().split(' ');
  
  for (const word of words) {
    // Try to play as a word animation first
    if (words[word]) {
      ref.animations.push(['add-text', word + ' ']);
      words[word](ref);
    } else {
      // Play character by character
      const characters = word.split('');
      characters.forEach((ch, index) => {
        if (index === characters.length - 1) {
          ref.animations.push(['add-text', ch + ' ']);
        } else {
          ref.animations.push(['add-text', ch]);
        }
        playAnimation(ref, ch);
      });
    }
  }
};

export const validateInput = (inputString) => {
  const validCharacters = /^[A-Za-z\s]*$/;
  return validCharacters.test(inputString);
};
```

#### 2.2.3 Convert Existing Alphabet Files to JSON
Python script to convert existing files (run once):
```python
import re
import json
import os

def parse_animation_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Extract animation arrays
    animations = []
    current_animation = []
    
    # Parse the push statements
    pattern = r'animations\.push\(\[(.*?)\]\);'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        parts = match.split(',')
        if len(parts) == 5:
            bone = parts[0].strip().strip('"')
            action = parts[1].strip().strip('"')
            axis = parts[2].strip().strip('"')
            limit = parts[3].strip()
            sign = parts[4].strip().strip('"')
            
            # Convert Math.PI expressions to decimals
            limit = eval(limit.replace('Math.PI', str(3.14159265359)))
            
            current_animation.append([bone, action, axis, limit, sign])
    
    return current_animation

# Process all alphabet files
alphabet_data = {}
alphabet_dir = 'client/src/Animations/Alphabets/'

for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
    filepath = os.path.join(alphabet_dir, f'{letter}.js')
    if os.path.exists(filepath):
        alphabet_data[letter] = parse_animation_file(filepath)

# Save to JSON
with open('client/src/Animations/Data/alphabetAnimations.json', 'w') as f:
    json.dump(alphabet_data, f, indent=2)
```

#### 2.2.4 Update Imports
Replace in all files that import alphabets:
```javascript
// OLD:
import * as alphabets from '../Animations/alphabets';

// Usage:
alphabets[ch](ref);

// NEW:
import { playAnimation, playString } from '../Animations/animationPlayer';

// Usage:
playAnimation(ref, ch);
// or
playString(ref, inputText);
```

**Raspberry Pi Benefits:**
- Reduces JavaScript bundle from ~2600 lines to ~200 lines + JSON
- JSON parses faster than executing functions
- Smaller memory footprint
- Enables lazy loading of animation data

---

## Phase 3: Improve Error Handling and User Feedback

### 3.1 Add Comprehensive Error Handling (Priority: HIGH)

#### 3.1.1 Create Error Toast Component
Create `client/src/Components/Common/ErrorToast.js`:
```javascript
import React, { useState, useEffect } from 'react';
import { Toast, ToastContainer } from 'react-bootstrap';

export const ErrorToast = ({ error, onClose }) => {
  const [show, setShow] = useState(true);
  
  useEffect(() => {
    if (error) {
      setShow(true);
    }
  }, [error]);
  
  const handleClose = () => {
    setShow(false);
    if (onClose) onClose();
  };
  
  if (!error) return null;
  
  return (
    <ToastContainer position="top-end" className="p-3">
      <Toast show={show} onClose={handleClose} delay={5000} autohide bg="danger">
        <Toast.Header>
          <strong className="me-auto">Error</strong>
        </Toast.Header>
        <Toast.Body className="text-white">
          {error.message || 'An unexpected error occurred'}
        </Toast.Body>
      </Toast>
    </ToastContainer>
  );
};
```

#### 3.1.2 Add Error Handling to API Calls
Update `client/src/Pages/Videos.js`:
```javascript
import { ErrorToast } from '../Components/Common/ErrorToast';

function Videos() {
  const [error, setError] = useState(null);
  
  const retrieveVideos = () => {
    axios
      .get(`${baseURL}/videos/all-videos`)
      .then((res) => {
        setVideos(res.data);
        setError(null);
      })
      .catch((err) => {
        const errorMessage = err.response?.data?.message || 
                           err.message || 
                           'Failed to load videos. Please check your connection.';
        setError({ message: errorMessage });
        console.error('Error fetching videos:', err);
      });
  };
  
  return (
    <>
      <ErrorToast error={error} onClose={() => setError(null)} />
      {/* ... rest of component ... */}
    </>
  );
}
```

Repeat pattern for:
- `client/src/Pages/Video.js` (video fetch)
- `client/src/Pages/CreateVideo.js` (video creation)

#### 3.1.3 Add Browser Support Detection
Create `client/src/Utils/browserSupport.js`:
```javascript
export const checkSpeechRecognitionSupport = () => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  return !!SpeechRecognition;
};

export const checkWebGLSupport = () => {
  try {
    const canvas = document.createElement('canvas');
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
    );
  } catch (e) {
    return false;
  }
};

export const getBrowserCapabilities = () => {
  return {
    speechRecognition: checkSpeechRecognitionSupport(),
    webGL: checkWebGLSupport(),
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    hardwareConcurrency: navigator.hardwareConcurrency || 1
  };
};
```

#### 3.1.4 Add Feature Detection to Components
Update `client/src/Pages/Convert.js`:
```javascript
import { checkSpeechRecognitionSupport } from '../Utils/browserSupport';

function Convert() {
  const [speechSupported, setSpeechSupported] = useState(true);
  
  useEffect(() => {
    const isSupported = checkSpeechRecognitionSupport();
    setSpeechSupported(isSupported);
    if (!isSupported) {
      console.warn('Speech recognition not supported in this browser');
    }
  }, []);
  
  // ... component code ...
  
  return (
    // ...
    {!speechSupported && (
      <div className="alert alert-warning">
        Speech recognition is not supported in your browser. 
        Please use text input or try a different browser.
      </div>
    )}
    // ... rest of JSX
  );
}
```

#### 3.1.5 Add Input Validation
Update animation player with validation:
```javascript
export const playString = (ref, inputString) => {
  // Validate input
  if (!validateInput(inputString)) {
    throw new Error(
      'Invalid input: Only letters and spaces are supported. ' +
      'Special characters and numbers are not yet supported.'
    );
  }
  
  // Sanitize and limit length for Raspberry Pi performance
  const sanitized = inputString.trim().slice(0, 500); // Max 500 chars
  
  if (sanitized.length === 0) {
    throw new Error('Please enter some text to animate');
  }
  
  // ... rest of function
};
```

---

### 3.2 Add Loading States (Priority: MEDIUM)

#### 3.2.1 Create Loading Spinner Component
Create `client/src/Components/Common/LoadingSpinner.js`:
```javascript
import React from 'react';
import { Spinner } from 'react-bootstrap';

export const LoadingSpinner = ({ message = 'Loading...', fullScreen = false }) => {
  const spinnerContent = (
    <div className="d-flex flex-column align-items-center justify-content-center p-4">
      <Spinner animation="border" variant="primary" />
      <p className="mt-3">{message}</p>
    </div>
  );
  
  if (fullScreen) {
    return (
      <div className="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center bg-white bg-opacity-75" style={{ zIndex: 9999 }}>
        {spinnerContent}
      </div>
    );
  }
  
  return spinnerContent;
};
```

#### 3.2.2 Add Loading State to Model Loading
Update `useThreeScene` hook:
```javascript
export const useThreeScene = (bot, canvasId = 'canvas', options = {}) => {
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    // ... existing setup code ...
    
    loader.load(
      bot,
      (gltf) => {
        // ... existing success handler ...
        setIsLoading(false);
        setLoadingProgress(100);
      },
      (xhr) => {
        const percentComplete = (xhr.loaded / xhr.total) * 100;
        setLoadingProgress(Math.round(percentComplete));
      },
      (error) => {
        console.error('Error loading model:', error);
        setIsLoading(false);
        setError({ message: 'Failed to load 3D model' });
      }
    );
    
    // ... cleanup ...
  }, [bot]);
  
  return { ref, isLoading, loadingProgress };
};
```

---

## Phase 4: Update Dependencies and Add Tooling

### 4.1 Update package.json (Priority: MEDIUM)

#### 4.1.1 Update Dependencies
Modify `client/package.json`:
```json
{
  "dependencies": {
    "@testing-library/jest-dom": "^5.17.0",
    "@testing-library/react": "^14.0.0",
    "@testing-library/user-event": "^14.5.1",
    "axios": "^1.6.2",
    "bootstrap": "^5.3.2",
    "font-awesome": "^4.7.0",
    "prop-types": "^15.8.1",
    "react": "^18.2.0",
    "react-bootstrap": "^2.9.1",
    "react-dom": "^18.2.0",
    "react-error-boundary": "^4.0.11",
    "react-input-slider": "^6.0.1",
    "react-router-dom": "^6.20.1",
    "react-scripts": "5.0.1",
    "react-speech-recognition": "^3.10.0",
    "three": "^0.160.0",
    "web-vitals": "^3.5.0"
  },
  "devDependencies": {
    "eslint": "^8.55.0",
    "eslint-config-react-app": "^7.0.1",
    "eslint-plugin-react": "^7.33.2",
    "eslint-plugin-react-hooks": "^4.6.0"
  }
}
```

**Update Process:**
```bash
cd client
npm install react@^18.2.0 react-dom@^18.2.0
npm install three@^0.160.0
npm install axios@^1.6.2
npm install react-router-dom@^6.20.1
npm install react-bootstrap@^2.9.1
npm install --save-dev eslint eslint-plugin-react eslint-plugin-react-hooks
```

#### 4.1.2 Handle React 18 Breaking Changes
Update `client/src/index.js`:
```javascript
// OLD (React 17):
import ReactDOM from 'react-dom';
ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);

// NEW (React 18):
import { createRoot } from 'react-dom/client';
const root = createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

---

### 4.2 Add ESLint Configuration (Priority: MEDIUM)

#### 4.2.1 Create ESLint Config
Create `.eslintrc.json`:
```json
{
  "extends": [
    "react-app",
    "react-app/jest"
  ],
  "rules": {
    "react-hooks/exhaustive-deps": "warn",
    "no-unused-vars": "warn",
    "react/prop-types": "warn",
    "no-console": ["warn", { "allow": ["warn", "error"] }]
  },
  "overrides": [
    {
      "files": ["**/*.test.js", "**/*.spec.js"],
      "env": {
        "jest": true
      }
    }
  ]
}
```

#### 4.2.2 Add PropTypes Validation
Example for VideoCard component:
```javascript
import PropTypes from 'prop-types';

function VideoCard({ video, handleClick }) {
  // ... component code ...
}

VideoCard.propTypes = {
  video: PropTypes.shape({
    _id: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    desc: PropTypes.string.isRequired,
    createdBy: PropTypes.string.isRequired,
    type: PropTypes.oneOf(['PUBLIC', 'PRIVATE']).isRequired
  }).isRequired,
  handleClick: PropTypes.func.isRequired
};

export default VideoCard;
```

Add PropTypes to all components with props.

---

### 4.3 Environment Variables (Priority: HIGH)

#### 4.3.1 Create Environment Files
Create `.env.development`:
```env
REACT_APP_API_URL=http://localhost:5000/sign-kit
REACT_APP_ENV=development
```

Create `.env.production`:
```env
REACT_APP_API_URL=https://sign-kit-api.herokuapp.com/sign-kit
REACT_APP_ENV=production
```

#### 4.3.2 Update Config File
Update `client/src/Config/config.js`:
```javascript
// OLD:
export const baseURL = 'https://sign-kit-api.herokuapp.com/sign-kit';

// NEW:
export const baseURL = process.env.REACT_APP_API_URL || 
                       'https://sign-kit-api.herokuapp.com/sign-kit';

export const isDevelopment = process.env.REACT_APP_ENV === 'development';

export const config = {
  apiUrl: baseURL,
  isDevelopment,
  // Raspberry Pi specific settings
  raspberryPi: {
    maxTextureSize: 2048, // Limit texture size
    pixelRatio: 1, // Force 1:1 pixel ratio
    antialias: false, // Disable antialiasing
    shadows: false, // Disable shadows
    maxAnimationLength: 500 // Character limit
  }
};
```

---

## Phase 5: Raspberry Pi Specific Optimizations

### 5.1 Performance Optimizations (Priority: CRITICAL for Pi)

#### 5.1.1 Reduce Rendering Quality
Update Three.js renderer settings:
```javascript
ref.renderer = new THREE.WebGLRenderer({ 
  antialias: false, // Disabled - too expensive for Pi
  powerPreference: 'low-power', // Critical for Pi
  precision: 'mediump', // Use medium precision
  stencil: false, // Disable stencil buffer
  depth: true,
  alpha: false // Opaque background is faster
});

// Force conservative pixel ratio
ref.renderer.setPixelRatio(1);

// Disable physically correct lights (expensive)
ref.renderer.physicallyCorrectLights = false;

// Reduce shadow map size if shadows are used
ref.renderer.shadowMap.enabled = false;
```

#### 5.1.2 Optimize Model Loading
Create `client/src/Utils/modelOptimizer.js`:
```javascript
export const optimizeModelForPi = (gltf) => {
  gltf.scene.traverse((child) => {
    if (child.isMesh) {
      // Disable frustum culling for animated meshes
      if (child.type === 'SkinnedMesh') {
        child.frustumCulled = false;
      }
      
      // Disable shadows (expensive on Pi)
      child.castShadow = false;
      child.receiveShadow = false;
      
      // Optimize materials
      if (child.material) {
        child.material.precision = 'mediump';
        child.material.fog = false;
        
        // Reduce texture quality if present
        if (child.material.map) {
          child.material.map.anisotropy = 1; // Disable anisotropic filtering
          child.material.map.generateMipmaps = false;
        }
      }
      
      // Simplify geometry if too complex
      if (child.geometry) {
        child.geometry.computeBoundingSphere();
        // Don't compute unnecessary attributes
        child.geometry.deleteAttribute('uv2');
      }
    }
  });
  
  return gltf.scene;
};
```

#### 5.1.3 Implement Model Caching
```javascript
// Cache loaded models to avoid reloading
const modelCache = new Map();

export const loadModelCached = (url, loader) => {
  return new Promise((resolve, reject) => {
    // Check cache first
    if (modelCache.has(url)) {
      resolve(modelCache.get(url).clone());
      return;
    }
    
    loader.load(
      url,
      (gltf) => {
        modelCache.set(url, gltf.scene);
        resolve(gltf.scene.clone());
      },
      undefined,
      reject
    );
  });
};
```

#### 5.1.4 Add Debouncing for User Input
Create `client/src/Utils/debounce.js`:
```javascript
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

export const throttle = (func, limit) => {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};
```

Use in components:
```javascript
import { debounce } from '../Utils/debounce';

const debouncedSign = useCallback(
  debounce((inputRef) => {
    sign(inputRef);
  }, 300),
  []
);
```

#### 5.1.5 Add Responsive Canvas Resize
```javascript
useEffect(() => {
  const handleResize = throttle(() => {
    if (!ref.camera || !ref.renderer) return;
    
    const width = window.innerWidth * 0.57;
    const height = window.innerHeight - 70;
    
    ref.camera.aspect = width / height;
    ref.camera.updateProjectionMatrix();
    ref.renderer.setSize(width, height);
  }, 250); // Throttle resize events
  
  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, [ref]);
```

---

### 5.2 Memory Management (Priority: CRITICAL for Pi)

#### 5.2.1 Implement Animation Queue Limits
```javascript
export const playString = (ref, inputString, maxQueueSize = 50) => {
  const sanitized = inputString.trim().slice(0, 500);
  
  // Prevent queue overflow on Raspberry Pi
  if (ref.animations.length > maxQueueSize) {
    throw new Error(
      `Animation queue is full (${maxQueueSize} animations). ` +
      'Please wait for current animations to complete.'
    );
  }
  
  // ... rest of function
};
```

#### 5.2.2 Add Memory Monitoring (Development Mode)
```javascript
export const checkMemoryUsage = () => {
  if (performance.memory) {
    const used = performance.memory.usedJSHeapSize;
    const limit = performance.memory.jsHeapSizeLimit;
    const percentage = (used / limit) * 100;
    
    if (percentage > 80) {
      console.warn(`High memory usage: ${percentage.toFixed(1)}%`);
    }
    
    return { used, limit, percentage };
  }
  return null;
};
```

#### 5.2.3 Implement Lazy Loading
Update routing in `App.js`:
```javascript
import { lazy, Suspense } from 'react';
import { LoadingSpinner } from './Components/Common/LoadingSpinner';

// Lazy load heavy components
const Convert = lazy(() => import('./Pages/Convert'));
const LearnSign = lazy(() => import('./Pages/LearnSign'));
const Video = lazy(() => import('./Pages/Video'));
const CreateVideo = lazy(() => import('./Pages/CreateVideo'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner fullScreen message="Loading page..." />}>
      <Routes>
        <Route path="/convert" element={<Convert />} />
        <Route path="/learn" element={<LearnSign />} />
        <Route path="/video/:id" element={<Video />} />
        <Route path="/create" element={<CreateVideo />} />
      </Routes>
    </Suspense>
  );
}
```

---

## Phase 6: Accessibility and UX Enhancements

### 6.1 Accessibility Improvements (Priority: MEDIUM)

#### 6.1.1 Add ARIA Labels
Update interactive elements:
```javascript
<button 
  className="btn btn-primary"
  onClick={startListening}
  aria-label="Start voice recognition"
  aria-pressed={listening}
>
  Mic On <i className="fa fa-microphone" aria-hidden="true" />
</button>

<textarea 
  rows={3} 
  value={text} 
  className='w-100 input-style' 
  readOnly
  aria-label="Processed text output"
  aria-live="polite"
/>

<canvas 
  id="canvas" 
  role="img" 
  aria-label="3D sign language animation viewer"
/>
```

#### 6.1.2 Add Keyboard Navigation
```javascript
const handleKeyPress = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sign(textFromInput);
  }
  
  if (event.key === 'Escape') {
    stopAnimation();
  }
};

<textarea
  onKeyDown={handleKeyPress}
  aria-describedby="keyboard-help"
/>
<small id="keyboard-help" className="form-text text-muted">
  Press Enter to start animation, Esc to stop
</small>
```

#### 6.1.3 Add Focus Indicators
Add to CSS:
```css
/* client/src/App.css */

/* Ensure visible focus indicators */
button:focus,
input:focus,
textarea:focus {
  outline: 2px solid #007bff;
  outline-offset: 2px;
}

/* Skip to main content link */
.skip-to-main {
  position: absolute;
  top: -40px;
  left: 0;
  background: #007bff;
  color: white;
  padding: 8px;
  z-index: 100;
}

.skip-to-main:focus {
  top: 0;
}
```

---

### 6.2 Animation Controls (Priority: MEDIUM)

#### 6.2.1 Add Playback Controls Component
Create `client/src/Components/Common/AnimationControls.js`:
```javascript
import React from 'react';
import { Button, ButtonGroup } from 'react-bootstrap';

export const AnimationControls = ({ 
  onPlay, 
  onPause, 
  onStop, 
  onReplay,
  isPlaying,
  disabled 
}) => {
  return (
    <ButtonGroup className="w-100 my-2">
      <Button 
        variant={isPlaying ? 'secondary' : 'primary'}
        onClick={onPlay}
        disabled={disabled || isPlaying}
        aria-label="Play animation"
      >
        <i className="fa fa-play" /> Play
      </Button>
      <Button 
        variant="warning"
        onClick={onPause}
        disabled={disabled || !isPlaying}
        aria-label="Pause animation"
      >
        <i className="fa fa-pause" /> Pause
      </Button>
      <Button 
        variant="danger"
        onClick={onStop}
        disabled={disabled}
        aria-label="Stop animation"
      >
        <i className="fa fa-stop" /> Stop
      </Button>
      <Button 
        variant="info"
        onClick={onReplay}
        disabled={disabled}
        aria-label="Replay animation"
      >
        <i className="fa fa-repeat" /> Replay
      </Button>
    </ButtonGroup>
  );
};
```

#### 6.2.2 Implement Control Logic
```javascript
const [isAnimating, setIsAnimating] = useState(false);
const [savedAnimations, setSavedAnimations] = useState([]);

const handlePlay = () => {
  if (ref.animations.length > 0 && !ref.pending) {
    setIsAnimating(true);
    ref.pending = true;
    ref.animate();
  }
};

const handlePause = () => {
  if (ref.animationFrameId) {
    cancelAnimationFrame(ref.animationFrameId);
    ref.pending = false;
    setIsAnimating(false);
  }
};

const handleStop = () => {
  handlePause();
  ref.animations = [];
  defaultPose(ref);
};

const handleReplay = () => {
  handleStop();
  ref.animations = [...savedAnimations];
  setTimeout(handlePlay, 100);
};
```

---

## Phase 7: Error Boundaries and Logging

### 7.1 Error Boundaries (Priority: HIGH)

#### 7.1.1 Create Error Boundary Component
Create `client/src/Components/Common/ErrorBoundary.js`:
```javascript
import React from 'react';
import { Button } from 'react-bootstrap';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo
    });
    
    // Log to error reporting service if configured
    if (window.errorLogger) {
      window.errorLogger.log(error, errorInfo);
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="container mt-5">
          <div className="alert alert-danger">
            <h2>Something went wrong</h2>
            <p>We're sorry, but something unexpected happened.</p>
            <details style={{ whiteSpace: 'pre-wrap' }}>
              {this.state.error && this.state.error.toString()}
              <br />
              {this.state.errorInfo && this.state.errorInfo.componentStack}
            </details>
            <Button variant="primary" onClick={this.handleReset} className="mt-3">
              Reload Page
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

#### 7.1.2 Wrap App with Error Boundary
Update `client/src/App.js`:
```javascript
import ErrorBoundary from './Components/Common/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <Router>
        {/* ... routes ... */}
      </Router>
    </ErrorBoundary>
  );
}
```

---

## Implementation Timeline

### Week 1: Critical Fixes
- Day 1-2: Memory leak fixes (Phase 1.1)
- Day 3-4: Null safety checks (Phase 1.2)
- Day 5: Testing on Raspberry Pi

### Week 2: Code Refactoring
- Day 1-3: Create and test custom hooks (Phase 2.1)
- Day 4-5: Refactor alphabet animations to JSON (Phase 2.2)

### Week 3: Error Handling & Updates
- Day 1-2: Add error handling and toasts (Phase 3.1)
- Day 3: Update dependencies (Phase 4.1)
- Day 4-5: Add ESLint and PropTypes (Phase 4.2-4.3)

### Week 4: Raspberry Pi Optimization
- Day 1-3: Implement performance optimizations (Phase 5.1)
- Day 4-5: Memory management and lazy loading (Phase 5.2)

### Week 5: Polish & Accessibility
- Day 1-2: Accessibility improvements (Phase 6.1)
- Day 3-4: Animation controls (Phase 6.2)
- Day 5: Error boundaries (Phase 7.1)

### Week 6: Testing & Documentation
- Day 1-3: Comprehensive testing on Raspberry Pi 4B
- Day 4-5: Performance benchmarking and documentation

---

## Raspberry Pi 4B Specific Testing Checklist

### Hardware Configuration
- [ ] Test on Pi 4B with 2GB RAM (minimum)
- [ ] Test on Pi 4B with 4GB RAM (recommended)
- [ ] Test on Pi 4B with 8GB RAM (optimal)

### Performance Metrics
- [ ] Measure FPS (target: 30+ FPS)
- [ ] Monitor memory usage (target: <1.5GB peak)
- [ ] Test animation queue performance (50+ animations)
- [ ] Measure model load time (target: <3 seconds)

### Browser Compatibility
- [ ] Chromium (default on Raspberry Pi OS)
- [ ] Firefox ESR
- [ ] Test with hardware acceleration enabled/disabled

### Features
- [ ] 3D model rendering smooth at 30 FPS
- [ ] All 26 alphabet animations work
- [ ] Word animations work
- [ ] Speech recognition (if supported)
- [ ] Text input animation
- [ ] Avatar switching
- [ ] Speed/pause controls

### Edge Cases
- [ ] Long text input (500 characters)
- [ ] Rapid animation triggering
- [ ] Tab switching and return
- [ ] Window resize
- [ ] Network errors
- [ ] Model loading failures

---

## Success Metrics

### Performance (Raspberry Pi 4B)
- **Frame Rate:** Maintain 30+ FPS during animations
- **Load Time:** 3D models load within 3 seconds
- **Memory Usage:** Peak usage <1.5GB RAM
- **Bundle Size:** JavaScript bundle <500KB gzipped

### Code Quality
- **Code Duplication:** Reduce from 96% to <10%
- **Lines of Code:** Reduce from ~3000 to ~1500
- **ESLint Errors:** 0 errors, <10 warnings
- **Test Coverage:** >70% for critical paths

### User Experience
- **Error Handling:** All API calls wrapped in try-catch
- **Loading States:** Visible feedback for all async operations
- **Accessibility:** WCAG 2.1 Level AA compliance
- **Browser Support:** Works in 95%+ of modern browsers

### Maintainability
- **PropTypes:** All components have type validation
- **Documentation:** All custom hooks documented
- **Environment Config:** No hardcoded URLs
- **Error Boundaries:** Graceful failure handling
