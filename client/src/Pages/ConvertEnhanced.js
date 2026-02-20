import '../App.css'
import React, { useState, useEffect, useRef } from "react";
import Slider from 'react-input-slider';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'font-awesome/css/font-awesome.min.css';

import xbot from '../Models/xbot/xbot.glb';
import ybot from '../Models/ybot/ybot.glb';
import xbotPic from '../Models/xbot/xbot.png';
import ybotPic from '../Models/ybot/ybot.png';

import { createEnhancedPlayer } from '../Services/enhancedAnimationPlayer';
import AudioRecorder from '../Services/audioRecorder';
import apiService from '../Services/apiService';

import { useThreeScene } from '../Hooks/useThreeScene';
import { useAnimationEngine } from '../Hooks/useAnimationEngine';

function Convert() {
  const [text, setText] = useState("");
  const [transcript, setTranscript] = useState("");
  const [bot, setBot] = useState(ybot);
  const [speed, setSpeed] = useState(1.0);
  const [pause, setPause] = useState(400);
  
  // Backend integration states
  const [isBackendMode, setIsBackendMode] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [backendStatus, setBackendStatus] = useState('checking');
  const [processingMessage, setProcessingMessage] = useState('');
  const [currentGloss, setCurrentGloss] = useState('');
  const [currentHamNoSys, setCurrentHamNoSys] = useState([]);
  
  // Refs
  let textFromInput = React.createRef();
  const audioRecorderRef = useRef(null);
  const animationPlayerRef = useRef(null);

  // Use custom hooks for Three.js scene and animation engine
  const ref = useThreeScene(bot, 'canvas');
  
  // Callback for text updates during animations
  const handleTextUpdate = (newText) => {
    setText(prevText => prevText + newText);
  };
  
  useAnimationEngine(ref, speed, pause, handleTextUpdate);

  // Initialize audio recorder and animation player
  useEffect(() => {
    const initializeServices = async () => {
      try {
        // Initialize audio recorder
        const recorder = new AudioRecorder();
        const initialized = await recorder.initialize({
          onTranscript: handleSpeechResult,
          onError: handleError,
          onProcessingStart: () => {
            setIsProcessing(true);
            setProcessingMessage('Processing audio...');
          },
          onProcessingEnd: () => {
            setIsProcessing(false);
            setProcessingMessage('');
          }
        });
        
        if (initialized) {
          audioRecorderRef.current = recorder;
        }

        // Initialize animation player
        if (ref) {
          animationPlayerRef.current = createEnhancedPlayer(ref);
          animationPlayerRef.current.setBackendMode(isBackendMode);
        }

        // Check backend health
        await checkBackendHealth();

      } catch (error) {
        console.error('Initialization error:', error);
        handleError('Failed to initialize services');
      }
    };

    initializeServices();

    // Cleanup
    return () => {
      if (audioRecorderRef.current) {
        audioRecorderRef.current.cleanup();
      }
    };
  }, [ref]);

  // Check backend health
  const checkBackendHealth = async () => {
    try {
      const health = await apiService.healthCheck();
      setBackendStatus(health.components?.gloss_mapper ? 'connected' : 'error');
    } catch (error) {
      console.error('Backend health check failed:', error);
      setBackendStatus('error');
    }
  };

  // Handle speech processing result
  const handleSpeechResult = async (result) => {
    try {
      setTranscript(result.original_text || '');
      setCurrentGloss(result.gloss || '');
      setCurrentHamNoSys(result.hamnosys || []);
      setText('');

      setProcessingMessage('Playing animation...');

      // Play animation using the ISL gloss (SOV order) from the backend
      if (animationPlayerRef.current && result.glosses && result.glosses.length > 0) {
        const glossText = result.glosses.join(' ');
        await animationPlayerRef.current._playTraditionalAnimation(glossText);
      } else if (animationPlayerRef.current && result.original_text) {
        // Fallback: play original transcript if no glosses returned
        await animationPlayerRef.current._playTraditionalAnimation(result.original_text);
      }

    } catch (error) {
      console.error('Error handling speech result:', error);
      handleError('Failed to process speech result');
    } finally {
      setProcessingMessage('');
    }
  };

  // Handle errors
  const handleError = (message) => {
    console.error('Error:', message);
    setProcessingMessage('');
    setIsProcessing(false);
    setIsRecording(false);
    alert(message);
  };

  // Handle text input with backend
  const handleTextInput = async () => {
    if (!textFromInput.current || !textFromInput.current.value.trim()) {
      alert('Please enter some text');
      return;
    }

    if (!animationPlayerRef.current) {
      alert('Animation player not ready');
      return;
    }

    try {
      setIsProcessing(true);
      setProcessingMessage('Processing text...');
      setText(''); // Clear text before starting

      const inputText = textFromInput.current.value.trim();
      
      if (isBackendMode) {
        // Use backend processing
        const result = await animationPlayerRef.current.playTextWithBackend(
          inputText,
          (progress) => setProcessingMessage(progress.message)
        );
        
        setCurrentGloss(result.gloss || '');
        setCurrentHamNoSys(result.hamnosys || []);
        setTranscript(result.original_text || '');
      } else {
        // Use traditional animation
        await animationPlayerRef.current._playTraditionalAnimation(inputText);
      }

    } catch (error) {
      console.error('Error processing text:', error);
      handleError('Failed to process text');
    } finally {
      setIsProcessing(false);
      setProcessingMessage('');
    }
  };

  // Handle recording
  const startRecording = () => {
    if (!audioRecorderRef.current) {
      alert('Audio recorder not ready');
      return;
    }

    audioRecorderRef.current.startRecording();
    setIsRecording(true);
    setTranscript('');
    setCurrentGloss('');
    setCurrentHamNoSys([]);
  };

  const stopRecording = () => {
    if (audioRecorderRef.current) {
      audioRecorderRef.current.stopRecording();
      setIsRecording(false);
    }
  };

  // Toggle backend mode
  const toggleBackendMode = () => {
    const newMode = !isBackendMode;
    setIsBackendMode(newMode);
    
    if (animationPlayerRef.current) {
      animationPlayerRef.current.setBackendMode(newMode);
    }
  };

  return (
    <div className='container-fluid'>
      <div className='row'>
        <div className='col-md-3'>
          {/* Backend Status */}
          <div className='backend-status mb-3'>
            <label className='label-style'>
              Backend Status: 
              <span className={`ml-2 ${backendStatus === 'connected' ? 'text-success' : backendStatus === 'error' ? 'text-danger' : 'text-warning'}`}>
                {backendStatus === 'connected' ? '✓ Connected' : backendStatus === 'error' ? '✗ Error' : '⚠ Checking...'}
              </span>
            </label>
            <button 
              className="btn btn-sm btn-outline-primary ml-2" 
              onClick={toggleBackendMode}
            >
              {isBackendMode ? 'Backend ON' : 'Backend OFF'}
            </button>
          </div>

          {/* Processing Status */}
          {isProcessing && (
            <div className='alert alert-info'>
              <i className="fa fa-spinner fa-spin"></i> {processingMessage}
            </div>
          )}

          {/* Results Display */}
          <label className='label-style'>
            Processed Text
          </label>
          <textarea rows={2} value={text} className='w-100 input-style' readOnly />
          
          {currentGloss && (
            <div className='mt-2'>
              <label className='label-style'>
                ISL Gloss
              </label>
              <textarea rows={1} value={currentGloss} className='w-100 input-style' readOnly />
            </div>
          )}

          {/* Speech Recognition */}
          <label className='label-style'>
            Speech Recognition: {isRecording ? 'recording...' : 'ready'}
          </label>
          <div className='space-between mb-2'>
            <button 
              className={`btn ${isRecording ? 'btn-danger' : 'btn-primary'} btn-style w-33`} 
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isProcessing}
            >
              {isRecording ? (
                <span>Stop <i className="fa fa-stop"/></span>
              ) : (
                <span>Mic <i className="fa fa-microphone"/></span>
              )}
            </button>
          </div>
          <textarea rows={2} value={transcript} placeholder='Speech input will appear here...' className='w-100 input-style' readOnly />

          {/* Text Input */}
          <label className='label-style'>
            Text Input
          </label>
          <textarea rows={3} ref={textFromInput} placeholder='Enter text to convert...' className='w-100 input-style' />
          <button 
            onClick={handleTextInput} 
            className='btn btn-primary w-100 btn-style btn-start'
            disabled={isProcessing}
          >
            {isProcessing ? (
              <span>Processing <i className="fa fa-spinner fa-spin"/></span>
            ) : (
              <span>Start Animation <i className="fa fa-play"/></span>
            )}
          </button>
        </div>

        <div className='col-md-7'>
          <div id='canvas'/>
        </div>

        <div className='col-md-2'>
          <p className='bot-label'>
            Select Avatar
          </p>
          <img src={xbotPic} className='bot-image col-md-11' onClick={()=>{setBot(xbot)}} alt='Avatar 1: XBOT'/>
          <img src={ybotPic} className='bot-image col-md-11' onClick={()=>{setBot(ybot)}} alt='Avatar 2: YBOT'/>
          
          <p className='label-style'>
            Animation Speed: {Math.round(speed*100)/100}
          </p>
          <Slider
            axis="x"
            xmin={0.05}
            xmax={1.0}
            xstep={0.01}
            x={speed}
            onChange={({ x }) => setSpeed(x)}
            className='w-100'
          />
          
          <p className='label-style'>
            Pause time: {pause} ms
          </p>
          <Slider
            axis="x"
            xmin={0}
            xmax={2000}
            xstep={100}
            x={pause}
            onChange={({ x }) => setPause(x)}
            className='w-100'
          />

          {/* Backend Info */}
          {isBackendMode && currentHamNoSys.length > 0 && (
            <div className='mt-3'>
              <p className='label-style'>
                HamNoSys Codes ({currentHamNoSys.length})
              </p>
              <div className='hamnosys-codes' style={{fontSize: '10px', maxHeight: '100px', overflowY: 'auto'}}>
                {currentHamNoSys.map((code, index) => (
                  <div key={index}>{code}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Convert;
