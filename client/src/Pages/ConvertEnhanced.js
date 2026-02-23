import '../App.css';
import React, { useState } from 'react';
import Slider from 'react-input-slider';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'font-awesome/css/font-awesome.min.css';

import xbot from '../Models/xbot/human1.glb';
import ybot from '../Models/ybot/ybot.glb';
import xbotPic from '../Models/xbot/xbot.png';
import ybotPic from '../Models/ybot/ybot.png';

import { playString } from '../Animations/animationPlayer';
import { convertToISLGloss } from '../Services/islGlossConverter';

import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';

import { useThreeScene } from '../Hooks/useThreeScene';
import { useAnimationEngine } from '../Hooks/useAnimationEngine';

/**
 * ConvertEnhanced page
 *
 * An enhanced version of Convert.js that runs typed/spoken English through
 * a client-side SVO → SOV grammar transformer (islGlossConverter.js) before
 * passing the reordered ISL gloss sequence to the 3-D avatar animation engine.
 *
 * Key additions over Convert.js:
 *   • "ISL Grammar (SOV)" toggle — when ON (default), text is converted to
 *     ISL gloss order before animation; when OFF, raw English order is used.
 *   • Gloss result panel showing original sentence ↓ ISL gloss string.
 *   • Both speech and text inputs are supported.
 */
function ConvertEnhanced() {
  const [text,        setText]        = useState('');
  const [bot,         setBot]         = useState(ybot);
  const [speed,       setSpeed]       = useState(1.0);
  const [pause,       setPause]       = useState(400);
  const [islMode,     setIslMode]     = useState(true);
  const [glossResult, setGlossResult] = useState(null); // { glosses, glossString, originalText }

  const textFromAudio = React.createRef();
  const textFromInput = React.createRef();

  const { transcript, listening, resetTranscript } = useSpeechRecognition();

  // Three.js scene and animation engine (same setup as Convert.js)
  const ref = useThreeScene(bot, 'canvas');

  const handleTextUpdate = (newText) => {
    setText(prev => prev + newText);
  };

  useAnimationEngine(ref, speed, pause, handleTextUpdate);

  // ── Sign handler ────────────────────────────────────────────────────────────
  const sign = (inputRef) => {
    const raw = inputRef.current.value;
    if (!raw.trim()) return;

    setText('');
    setGlossResult(null);

    try {
      if (islMode) {
        // SVO → SOV: convert to ISL gloss, then animate
        const result = convertToISLGloss(raw);
        setGlossResult(result);
        playString(ref, result.glosses.join(' '), true);
      } else {
        // Direct mode: pass raw English text (same behaviour as Convert.js)
        playString(ref, raw, true);
      }
    } catch (error) {
      console.error('Animation error:', error.message);
      alert(error.message);
    }
  };

  const startListening = () => SpeechRecognition.startListening({ continuous: true });
  const stopListening  = () => SpeechRecognition.stopListening();

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className='container-fluid'>
      <div className='row'>

        {/* ── Left panel ──────────────────────────────────────────────────── */}
        <div className='col-md-3'>

          {/* ISL Grammar toggle */}
          <div className='d-flex align-items-center justify-content-between mt-3 mb-2'>
            <label className='label-style mb-0' htmlFor='islModeSwitch'>
              ISL Grammar (SOV)
            </label>
            <div className='form-check form-switch ms-2 mb-0'>
              <input
                className='form-check-input'
                type='checkbox'
                role='switch'
                id='islModeSwitch'
                checked={islMode}
                onChange={e => { setIslMode(e.target.checked); setGlossResult(null); }}
                style={{ cursor: 'pointer' }}
              />
            </div>
          </div>

          {/* ISL Gloss result panel (shown after conversion) */}
          {glossResult && (
            <div
              className='mb-2 p-2'
              style={{
                background: '#1a1a2e',
                border: '1px solid #4a4a8a',
                borderRadius: 6,
                wordBreak: 'break-word',
              }}
            >
              <div style={{ fontSize: '0.72rem', color: '#999', marginBottom: 2 }}>
                English (SVO)
              </div>
              <div style={{ color: '#ccc', fontSize: '0.85rem', fontStyle: 'italic', marginBottom: 6 }}>
                {glossResult.originalText}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#999', marginBottom: 2 }}>
                ↓ ISL Gloss (SOV)
              </div>
              <div style={{ color: '#7ec8e3', fontWeight: 'bold', letterSpacing: 1, fontSize: '0.9rem' }}>
                {glossResult.glossString || <span style={{ color: '#888', fontWeight: 'normal' }}>—</span>}
              </div>
              <div style={{ fontSize: '0.68rem', color: '#666', marginTop: 4 }}>
                {glossResult.glosses.length} gloss{glossResult.glosses.length !== 1 ? 'es' : ''}
              </div>
            </div>
          )}

          {/* Animated text readout */}
          <label className='label-style'>Animated Text</label>
          <textarea rows={2} value={text} className='w-100 input-style' readOnly />

          {/* Speech recognition */}
          <label className='label-style'>
            Speech Recognition: {listening ? 'on' : 'off'}
          </label>
          <div className='space-between'>
            <button className='btn btn-primary btn-style w-33' onClick={startListening}>
              Mic On <i className='fa fa-microphone' />
            </button>
            <button className='btn btn-primary btn-style w-33' onClick={stopListening}>
              Mic Off <i className='fa fa-microphone-slash' />
            </button>
            <button className='btn btn-primary btn-style w-33' onClick={resetTranscript}>
              Clear
            </button>
          </div>
          <textarea
            rows={3}
            ref={textFromAudio}
            value={transcript}
            placeholder='Speech input …'
            className='w-100 input-style'
            readOnly
          />
          <button onClick={() => sign(textFromAudio)} className='btn btn-primary w-100 btn-style btn-start'>
            Start Animations
          </button>

          {/* Text input */}
          <label className='label-style'>Text Input</label>
          <textarea rows={3} ref={textFromInput} placeholder='Text input …' className='w-100 input-style' />
          <button onClick={() => sign(textFromInput)} className='btn btn-primary w-100 btn-style btn-start'>
            Start Animations
          </button>
        </div>

        {/* ── Three.js canvas ─────────────────────────────────────────────── */}
        <div className='col-md-7'>
          <div id='canvas' />
        </div>

        {/* ── Right panel ─────────────────────────────────────────────────── */}
        <div className='col-md-2'>
          <p className='bot-label'>Select Avatar</p>
          <img
            src={xbotPic}
            className='bot-image col-md-11'
            onClick={() => setBot(xbot)}
            alt='Avatar 1: XBOT'
          />
          <img
            src={ybotPic}
            className='bot-image col-md-11'
            onClick={() => setBot(ybot)}
            alt='Avatar 2: YBOT'
          />

          <p className='label-style'>Animation Speed: {Math.round(speed * 100) / 100}</p>
          <Slider
            axis='x'
            xmin={0.05}
            xmax={1.0}
            xstep={0.01}
            x={speed}
            onChange={({ x }) => setSpeed(x)}
            className='w-100'
          />

          <p className='label-style'>Pause time: {pause} ms</p>
          <Slider
            axis='x'
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
  );
}

export default ConvertEnhanced;
