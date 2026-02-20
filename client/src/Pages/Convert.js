import '../App.css'
import React, { useState } from "react";
import Slider from 'react-input-slider';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'font-awesome/css/font-awesome.min.css';

import xbot from '../Models/xbot/human1.glb';
import ybot from '../Models/ybot/ybot.glb';
import xbotPic from '../Models/xbot/xbot.png';
import ybotPic from '../Models/ybot/ybot.png';

import { playString } from '../Animations/animationPlayer';

import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';

import { useThreeScene } from '../Hooks/useThreeScene';
import { useAnimationEngine } from '../Hooks/useAnimationEngine';

function Convert() {
  const [text, setText] = useState("");
  const [bot, setBot] = useState(ybot);
  const [speed, setSpeed] = useState(1.0);
  const [pause, setPause] = useState(400);

  let textFromAudio = React.createRef();
  let textFromInput = React.createRef();

  const {
    transcript,
    listening,
    resetTranscript,
  } = useSpeechRecognition();

  // Use custom hooks for Three.js scene and animation engine
  const ref = useThreeScene(bot, 'canvas');
  
  // Callback for text updates during animations
  const handleTextUpdate = (newText) => {
    setText(prevText => prevText + newText);
  };
  
  useAnimationEngine(ref, speed, pause, handleTextUpdate);

  const sign = (inputRef) => {
    const str = inputRef.current.value;
    setText(''); // Clear text before starting new animation
    
    try {
      playString(ref, str, true);
    } catch (error) {
      console.error('Animation error:', error.message);
      alert(error.message);
    }
  }

  const startListening = () =>{
    SpeechRecognition.startListening({continuous: true});
  }

  const stopListening = () =>{
    SpeechRecognition.stopListening();
  }

  return (
    <div className='container-fluid'>
      <div className='row'>
        <div className='col-md-3'>
          <label className='label-style'>
            Processed Text
          </label>
          <textarea rows={3} value={text} className='w-100 input-style' readOnly />
          <label className='label-style'>
            Speech Recognition: {listening ? 'on' : 'off'}
          </label>
          <div className='space-between'>
            <button className="btn btn-primary btn-style w-33" onClick={startListening}>
              Mic On <i className="fa fa-microphone"/>
            </button>
            <button className="btn btn-primary btn-style w-33" onClick={stopListening}>
              Mic Off <i className="fa fa-microphone-slash"/>
            </button>
            <button className="btn btn-primary btn-style w-33" onClick={resetTranscript}>
              Clear
            </button>
          </div>
          <textarea rows={3} ref={textFromAudio} value={transcript} placeholder='Speech input ...' className='w-100 input-style' />
          <button onClick={() => {sign(textFromAudio)}} className='btn btn-primary w-100 btn-style btn-start'>
            Start Animations
          </button>
          <label className='label-style'>
            Text Input
          </label>
          <textarea rows={3} ref={textFromInput} placeholder='Text input ...' className='w-100 input-style' />
          <button onClick={() => {sign(textFromInput)}} className='btn btn-primary w-100 btn-style btn-start'>
            Start Animations
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
        </div>
      </div>
    </div>
  )
}

export default Convert;