import '../App.css'
import React, { useState } from "react";
import Slider from 'react-input-slider';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'font-awesome/css/font-awesome.min.css';

import xbot from '../Models/xbot/xbot.glb';
import ybot from '../Models/ybot/ybot.glb';
import xbotPic from '../Models/xbot/xbot.png';
import ybotPic from '../Models/ybot/ybot.png';

import * as words from '../Animations/words';
import { playAnimation, playWord } from '../Animations/animationPlayer';

import { useThreeScene } from '../Hooks/useThreeScene';
import { useAnimationEngine } from '../Hooks/useAnimationEngine';

function LearnSign() {
  const [bot, setBot] = useState(ybot);
  const [speed, setSpeed] = useState(1.0);
  const [pause, setPause] = useState(400);

  // Use custom hooks for Three.js scene and animation engine
  const ref = useThreeScene(bot, 'canvas');
  useAnimationEngine(ref, speed, pause);

  let alphaButtons = [];
  for (let i = 0; i < 26; i++) {
    const letter = String.fromCharCode(i + 65);
    alphaButtons.push(
        <div className='col-md-3' key={`alpha-${letter}`}>
            <button className='signs w-100' onClick={()=>{
              if(ref.animations.length === 0){
                playAnimation(ref, letter);
              }
            }}>
                {letter}
            </button>
        </div>
    );
  }

  let wordButtons = [];
  for (let i = 0; i < words.wordList.length; i++) {
    const word = words.wordList[i];
    wordButtons.push(
        <div className='col-md-4' key={`word-${word}`}>
            <button className='signs w-100' onClick={()=>{
              if(ref.animations.length === 0){
                playWord(ref, word);
              }
            }}>
                {word}
            </button>
        </div>
    );
  }

  return (
    <div className='container-fluid'>
      <div className='row'>
        <div className='col-md-3'>
            <h1 className='heading'>
              Alphabets
            </h1>
            <div className='row'>
                {
                    alphaButtons
                }
            </div>
            <h1 className='heading'>
              Words
            </h1>
            <div className='row'>
                {
                    wordButtons
                }
            </div>
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

export default LearnSign;
