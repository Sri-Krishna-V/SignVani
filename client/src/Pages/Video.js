import '../App.css'
import axios from 'axios';
import React, { useState, useEffect, useRef } from "react";
import { useParams } from 'react-router-dom'
import Slider from 'react-input-slider';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'font-awesome/css/font-awesome.min.css';

import xbot from '../Models/xbot/xbot.glb';
import ybot from '../Models/ybot/ybot.glb';
import xbotPic from '../Models/xbot/xbot.png';
import ybotPic from '../Models/ybot/ybot.png';

import { playString } from '../Animations/animationPlayer';

import { Button, Modal } from "react-bootstrap";

import { baseURL } from '../Config/config'

import { useThreeScene } from '../Hooks/useThreeScene';
import { useAnimationEngine } from '../Hooks/useAnimationEngine';


function Video() {
  const [text, setText] = useState("");
  const [bot, setBot] = useState(ybot);
  const [speed, setSpeed] = useState(1.0);
  const [pause, setPause] = useState(400);
  const [invalidId, setInvalidId] = useState(false)
  const [title, setTitle] = useState('')
  const [desc, setDesc] = useState('')

  const params = useParams()

  const id = useRef();

  // Use custom hooks for Three.js scene and animation engine
  const ref = useThreeScene(bot, 'canvas');
  
  // Callback for text updates during animations
  const handleTextUpdate = (newText) => {
    setText(prevText => prevText + newText);
  };
  
  useAnimationEngine(ref, speed, pause, handleTextUpdate);

  useEffect(() => {
    id.current.value = params.videoId;
  }, [params.videoId]);

  const sign = (str) => {
    setText(''); // Clear text before starting new animation
    
    try {
      playString(ref, str, true);
    } catch (error) {
      console.error('Animation error:', error.message);
      alert(error.message);
    }
  }

  const animateFromID = () => {
      const videoID = id.current.value;
      axios.get(`${baseURL}/videos/${videoID}`).then((res) => {
        console.log(res.data)
        setTitle(res.data.title)
        setDesc(res.data.desc)
        sign(res.data.content);
      }).catch(err => {
        console.log(err)
        setInvalidId(true)
      });
  }

  return (
    <div className='container-fluid'>
      <div className='row'>
        <div className='col-md-3'>
          <label className='label-style'>
              Video ID
          </label>
          <input ref={id} splaceholder='Video ID' className='w-100 input-style' />
          <button onClick={animateFromID} className='btn btn-primary w-100 btn-style btn-start mb-3'>
              Start Video
          </button>
          <hr />
          {title && 
            <div className='d-flex flex-column justify-content-center align-items-center mt-3'>
            <label className='h3'>{title}</label>
            <label>{desc}</label>
            <div className='w-100'>
              <label className='label-style mt-4'>
                Processed Text
              </label>
              <textarea rows={10} value={text} className='w-100 input-style mt-2' readOnly />
              </div>
          </div>}
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
      <Modal show={invalidId} onHide={() => setInvalidId(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Invalid Video ID</Modal.Title>
        </Modal.Header>
        <Modal.Body>Please make sure that the video ID that your have entered is valid!</Modal.Body>
        <Modal.Footer>
          <Button variant="primary" onClick={() => setInvalidId(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  )
}

export default Video;