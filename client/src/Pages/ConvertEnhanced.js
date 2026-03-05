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
import apiService from '../Services/apiService';

import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';

import { useThreeScene } from '../Hooks/useThreeScene';
import { useAnimationEngine } from '../Hooks/useAnimationEngine';

/**
 * ConvertEnhanced page
 *
 * An enhanced version of Convert.js that sends English text to the NLP
 * backend (/api/text-to-sign) for full ISL grammar processing (tense markers,
 * negation reordering, question classification) and animates the returned
 * gloss sequence on the 3-D avatar.
 *
 * Key features:
 *   • "ISL Grammar (SOV)" toggle — when ON (default), text is sent to the
 *     backend; when OFF, raw English order is used directly.
 *   • Gloss result panel showing original sentence ↓ ISL gloss string, plus
 *     grammar metadata badges: tense, negation, question type.
 *   • Falls back to the offline islGlossConverter when the backend is
 *     unreachable (network error or 5xx).
 *   • Both speech and text inputs are supported.
 */
function ConvertEnhanced() {
  const [text,         setText]         = useState('');
  const [bot,          setBot]          = useState(ybot);
  const [speed,        setSpeed]        = useState(1.0);
  const [pause,        setPause]        = useState(400);
  const [islMode,      setIslMode]      = useState(true);
  const [isLoading,    setIsLoading]    = useState(false);
  const [backendError, setBackendError] = useState(null);
  // glossResult: { glosses, glossString, originalText, tense, is_negated, question_type, source }
  const [glossResult,  setGlossResult]  = useState(null);

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
  const sign = async (inputRef) => {
    const raw = inputRef.current.value;
    if (!raw.trim()) return;

    // Clear any queued/in-progress animations from prior calls
    ref.animations = [];
    ref.pending = false;

    setText('');
    setGlossResult(null);
    setBackendError(null);

    if (!islMode) {
      // Direct mode: pass raw English text (same behaviour as Convert.js)
      playString(ref, raw, true);
      return;
    }

    // ISL Grammar mode — try backend first, fall back to local converter
    setIsLoading(true);
    try {
      const apiResult = await apiService.textToSign(raw);
      const result = {
        glosses:       apiResult.glosses      || [],
        glossString:   apiResult.gloss        || '',
        originalText:  apiResult.original_text || raw,
        tense:         apiResult.tense        ?? null,
        is_negated:    apiResult.is_negated   ?? false,
        question_type: apiResult.question_type ?? null,
        source: 'backend',
      };
      setGlossResult(result);
      playString(ref, result.glosses.join(' '), true);
    } catch (err) {
      console.warn('Backend unavailable, falling back to local converter:', err.message);
      setBackendError('Backend unreachable — using offline converter.');
      try {
        const local = convertToISLGloss(raw);
        setGlossResult({ ...local, tense: null, is_negated: false, question_type: null, source: 'local' });
        playString(ref, local.glosses.join(' '), true);
      } catch (animError) {
        console.error('Animation error:', animError.message);
        alert(animError.message);
      }
    } finally {
      setIsLoading(false);
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

          {/* Loading indicator */}
          {isLoading && (
            <div className='mb-2 p-2 text-center' style={{ color: '#7ec8e3', fontSize: '0.8rem' }}>
              <span className='spinner-border spinner-border-sm me-1' role='status' aria-hidden='true' />
              Processing…
            </div>
          )}

          {/* Backend fallback warning */}
          {backendError && (
            <div className='mb-2 p-1' style={{ background: '#2a1a00', border: '1px solid #a06000', borderRadius: 4, fontSize: '0.72rem', color: '#f0a030' }}>
              ⚠ {backendError}
            </div>
          )}

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

              {/* Grammar metadata badges (Phase 1–3) */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 6 }}>
                {glossResult.tense && (
                  <span style={{
                    background: glossResult.tense === 'PAST' ? '#2e1a4a' : '#1a2e4a',
                    color:      glossResult.tense === 'PAST' ? '#cc88ff' : '#88ccff',
                    border:     `1px solid ${glossResult.tense === 'PAST' ? '#7744bb' : '#4488bb'}`,
                    borderRadius: 4, fontSize: '0.68rem', padding: '1px 6px',
                  }}>
                    {glossResult.tense}
                  </span>
                )}
                {glossResult.is_negated && (
                  <span style={{
                    background: '#3a1010', color: '#ff7070',
                    border: '1px solid #aa3030',
                    borderRadius: 4, fontSize: '0.68rem', padding: '1px 6px',
                  }}>
                    NEGATED
                  </span>
                )}
                {glossResult.question_type && (
                  <span style={{
                    background: '#1a3a20', color: '#70ee90',
                    border: '1px solid #30aa50',
                    borderRadius: 4, fontSize: '0.68rem', padding: '1px 6px',
                  }}>
                    {glossResult.question_type === 'WH' ? 'WH-question' : 'Yes/No question'}
                  </span>
                )}
                <span style={{ color: '#444', fontSize: '0.65rem', alignSelf: 'center' }}>
                  {glossResult.glosses.length} gloss{glossResult.glosses.length !== 1 ? 'es' : ''}
                  {glossResult.source === 'local' ? ' · offline' : ''}
                </span>
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
          <button onClick={() => sign(textFromAudio)} disabled={isLoading} className='btn btn-primary w-100 btn-style btn-start'>
            Start Animations
          </button>

          {/* Text input */}
          <label className='label-style'>Text Input</label>
          <textarea rows={3} ref={textFromInput} placeholder='Text input …' className='w-100 input-style' />
          <button onClick={() => sign(textFromInput)} disabled={isLoading} className='btn btn-primary w-100 btn-style btn-start'>
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
