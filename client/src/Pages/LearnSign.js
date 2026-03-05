import '../App.css'
import React, { useState, useEffect, useRef, useCallback } from "react";
import Slider from 'react-input-slider';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'font-awesome/css/font-awesome.min.css';

import xbot from '../Models/xbot/human1.glb';
import ybot from '../Models/ybot/ybot.glb';
import xbotPic from '../Models/xbot/xbot.png';
import ybotPic from '../Models/ybot/ybot.png';

import * as words from '../Animations/words';
import { playAnimation, playWord } from '../Animations/animationPlayer';
import { getWordDescription } from '../Animations/Utils/wordLoader';

import { useThreeScene } from '../Hooks/useThreeScene';
import { useAnimationEngine } from '../Hooks/useAnimationEngine';

// ── Category definitions ────────────────────────────────────────────────────
const CATEGORIES = [
  { label: 'Greetings',       color: '#4CAF50', words: ['HELLO','HI','BYE','WELCOME','THANK','PLEASE','SORRY','PLEASE_NAMASTE'] },
  { label: 'Pronouns',        color: '#2196F3', words: ['I','ME','YOU'] },
  { label: 'Common Verbs',    color: '#9C27B0', words: ['GO','COME','EAT','DRINK','LOVE','SEE','KNOW','WANT','HELP','UNDERSTAND','DO','READ','PLAY','LIKE','FINISH'] },
  { label: 'People & Family', color: '#FF9800', words: ['PERSON','NAME','FAMILY','FRIEND','MOTHER','FATHER','BROTHER','SISTER','TEACHER'] },
  { label: 'Nouns',           color: '#00BCD4', words: ['HOME','SCHOOL','WORK','WATER','FOOD','MONEY'] },
  { label: 'Emotions',        color: '#E91E63', words: ['HAPPY','SAD','GOOD','BAD','TIRED','SICK','ANGRY','SCARED','HUNGRY','THIRSTY','BORED','EXCITED'] },
  { label: 'Time',            color: '#607D8B', words: ['TIME','TODAY','TOMORROW','YESTERDAY','MORNING','NIGHT','NOW','LATER','AGAIN'] },
  { label: 'Questions',       color: '#FF5722', words: ['WHAT','WHERE','WHEN','WHO','WHY','HOW','WHICH'] },
  { label: 'Responses',       color: '#795548', words: ['YES','NO','CAN','STOP','WAIT'] },
  { label: 'Directions',      color: '#009688', words: ['LEFT','RIGHT','UP','DOWN','NEAR','FAR','FRONT','BACK','INSIDE'] },
];

// Speed presets
const PRESETS = [
  { label: 'Beginner', speed: 0.3,  pause: 900 },
  { label: 'Normal',   speed: 1.0,  pause: 400 },
  { label: 'Expert',   speed: 1.0,  pause: 100 },
];

function LearnSign() {
  const [bot,         setBot]         = useState(ybot);
  const [speed,       setSpeed]       = useState(1.0);
  const [pause,       setPause]       = useState(400);
  const [tab,         setTab]         = useState('alphabets'); // 'alphabets' | 'words' | 'categories'
  const [search,      setSearch]      = useState('');
  const [playing,     setPlaying]     = useState(null);   // currently playing key
  const [lastPlayed,  setLastPlayed]  = useState(null);   // { type, key } for replay
  const [description, setDescription] = useState('');
  const [preset,      setPreset]      = useState('Normal');

  const pollerRef = useRef(null);

  const ref = useThreeScene(bot, 'canvas');
  useAnimationEngine(ref, speed, pause);

  // ── Poll animation queue to detect when playing finishes ─────────────────
  const startPolling = useCallback((key) => {
    setPlaying(key);
    if (pollerRef.current) clearInterval(pollerRef.current);
    pollerRef.current = setInterval(() => {
      if (ref.animations && ref.animations.length === 0 && !ref.pending) {
        setPlaying(null);
        clearInterval(pollerRef.current);
      }
    }, 100);
  }, [ref]);

  useEffect(() => () => { if (pollerRef.current) clearInterval(pollerRef.current); }, []);

  // ── Play helpers ──────────────────────────────────────────────────────────
  const signLetter = useCallback((letter) => {
    if (playing) return;
    playAnimation(ref, letter);
    setLastPlayed({ type: 'letter', key: letter });
    setDescription(`Fingerspelling: ${letter}`);
    startPolling(letter);
  }, [playing, ref, startPolling]);

  const signWord = useCallback((word) => {
    if (playing) return;
    playWord(ref, word);
    setLastPlayed({ type: 'word', key: word });
    setDescription(getWordDescription(word));
    startPolling(word);
  }, [playing, ref, startPolling]);

  const replay = useCallback(() => {
    if (!lastPlayed || playing) return;
    if (lastPlayed.type === 'letter') signLetter(lastPlayed.key);
    else signWord(lastPlayed.key);
  }, [lastPlayed, playing, signLetter, signWord]);

  // ── Keyboard shortcut: A–Z triggers letter sign ───────────────────────────
  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === 'INPUT') return;
      if (e.key.length === 1 && e.key.match(/[a-zA-Z]/)) {
        signLetter(e.key.toUpperCase());
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [signLetter]);

  // ── Apply speed preset ────────────────────────────────────────────────────
  const applyPreset = (p) => {
    setPreset(p.label);
    setSpeed(p.speed);
    setPause(p.pause);
  };

  // ── Filter helpers ────────────────────────────────────────────────────────
  const q = search.toUpperCase().trim();
  const filteredLetters = Array.from({ length: 26 }, (_, i) => String.fromCharCode(i + 65))
    .filter(l => !q || l.startsWith(q));
  const filteredWords = words.wordList.filter(w => !q || w.includes(q));

  // ── Shared button renderer ────────────────────────────────────────────────
  const renderLetterBtn = (letter) => {
    const isActive = playing === letter;
    return (
      <div className='col-3 p-1' key={`alpha-${letter}`}>
        <button
          className='w-100 learn-btn'
          style={isActive ? activeBtnStyle : btnStyle}
          title={`Fingerspell: ${letter}`}
          onClick={() => signLetter(letter)}
        >
          {isActive ? <span className='learn-pulse'/> : null}
          {letter}
        </button>
      </div>
    );
  };

  const renderWordBtn = (word, accentColor) => {
    const isActive = playing === word;
    const desc = getWordDescription(word);
    return (
      <div className='col-6 p-1' key={`word-${word}`}>
        <button
          className='w-100 learn-btn'
          style={isActive ? { ...activeBtnStyle, borderColor: accentColor || '#7ec8e3' }
                          : { ...btnStyle,   borderColor: accentColor || '#444' }}
          title={desc}
          onClick={() => signWord(word)}
        >
          {isActive ? <span className='learn-pulse'/> : null}
          <span style={{ fontSize: '0.75rem', fontWeight: 600, letterSpacing: 0.5 }}>
            {word.replace('_', ' ')}
          </span>
        </button>
      </div>
    );
  };

  // ── Tab content ───────────────────────────────────────────────────────────
  const tabContent = () => {
    if (tab === 'alphabets') {
      return (
        <div className='row g-0'>
          {filteredLetters.length > 0
            ? filteredLetters.map(renderLetterBtn)
            : <p className='text-muted text-center mt-3' style={{fontSize:'0.85rem'}}>No match</p>
          }
        </div>
      );
    }
    if (tab === 'words') {
      return (
        <div className='row g-0'>
          {filteredWords.length > 0
            ? filteredWords.map(w => renderWordBtn(w, null))
            : <p className='text-muted text-center mt-3' style={{fontSize:'0.85rem'}}>No match</p>
          }
        </div>
      );
    }
    if (tab === 'categories') {
      return CATEGORIES.map(cat => {
        const catWords = cat.words.filter(
          w => words.wordList.includes(w) && (!q || w.includes(q))
        );
        if (catWords.length === 0) return null;
        return (
          <div key={cat.label} className='mb-3'>
            <div style={{
              fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase',
              letterSpacing: 1, color: cat.color, borderBottom: `2px solid ${cat.color}`,
              paddingBottom: 3, marginBottom: 6
            }}>
              {cat.label}
            </div>
            <div className='row g-0'>
              {catWords.map(w => renderWordBtn(w, cat.color))}
            </div>
          </div>
        );
      });
    }
  };

  // ── Styles ────────────────────────────────────────────────────────────────
  const btnStyle = {
    background: '#1e1e2e', color: '#ddd',
    border: '1px solid #444', borderRadius: 6,
    padding: '6px 4px', cursor: 'pointer',
    fontSize: '0.85rem', position: 'relative',
    transition: 'border-color 0.15s, background 0.15s',
  };
  const activeBtnStyle = {
    ...btnStyle, background: '#2a3a4a', color: '#fff',
    borderColor: '#7ec8e3', boxShadow: '0 0 6px #7ec8e355',
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <>
      {/* Inline styles for pulse animation + scrollable panel */}
      <style>{`
        .learn-panel { height: calc(100vh - 120px); overflow-y: auto; scrollbar-width: thin; }
        .learn-btn:hover { background: #2a2a3e !important; color: #fff !important; }
        @keyframes pulse-ring {
          0%   { box-shadow: 0 0 0 0 rgba(126,200,227,0.6); }
          70%  { box-shadow: 0 0 0 6px rgba(126,200,227,0); }
          100% { box-shadow: 0 0 0 0 rgba(126,200,227,0); }
        }
        .learn-pulse {
          position: absolute; inset: 0; border-radius: 6px;
          animation: pulse-ring 1s infinite;
          pointer-events: none;
        }
      `}</style>

      <div className='container-fluid'>
        <div className='row'>

          {/* ── Left: selector panel ──────────────────────────────────────── */}
          <div className='col-md-3 learn-panel'>

            {/* Tabs */}
            <div className='d-flex mt-3 mb-2' style={{ gap: 4 }}>
              {['alphabets','words','categories'].map(t => (
                <button
                  key={t}
                  onClick={() => { setTab(t); setSearch(''); }}
                  style={{
                    flex: 1, padding: '6px 4px', borderRadius: 6, cursor: 'pointer',
                    fontSize: '0.78rem', fontWeight: 600, textTransform: 'capitalize',
                    background: tab === t ? '#2196F3' : '#1e1e2e',
                    color: tab === t ? '#fff' : '#aaa',
                    border: tab === t ? '1px solid #2196F3' : '1px solid #444',
                  }}
                >
                  {t}
                </button>
              ))}
            </div>

            {/* Search */}
            <div className='mb-2' style={{ position: 'relative' }}>
              <input
                type='text'
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder={`Search ${tab}…`}
                style={{
                  width: '100%', padding: '6px 30px 6px 10px',
                  background: '#1e1e2e', color: '#ddd',
                  border: '1px solid #444', borderRadius: 6,
                  fontSize: '0.85rem', outline: 'none',
                }}
              />
              {search && (
                <button
                  onClick={() => setSearch('')}
                  style={{
                    position: 'absolute', right: 6, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', color: '#888', cursor: 'pointer', fontSize: '1rem',
                  }}
                >×</button>
              )}
            </div>

            {/* Tab content */}
            {tabContent()}
          </div>

          {/* ── Centre: canvas ────────────────────────────────────────────── */}
          <div className='col-md-7' style={{ position: 'relative' }}>

            {/* Description + replay bar */}
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              minHeight: 36, padding: '4px 8px', marginBottom: 4,
              background: '#1a1a2e', borderRadius: 6,
              border: '1px solid #333',
            }}>
              <span style={{
                fontSize: '0.82rem', color: playing ? '#7ec8e3' : '#666',
                fontStyle: description ? 'normal' : 'italic', flex: 1,
              }}>
                {playing
                  ? <>
                      <span style={{ color: '#7ec8e3', fontWeight: 700, marginRight: 8 }}>
                        {playing.replace('_', ' ')}
                      </span>
                      <span style={{ color: '#aaa' }}>{description}</span>
                    </>
                  : (lastPlayed
                      ? <span style={{ color: '#666' }}>
                          Last: <strong style={{ color: '#999' }}>{lastPlayed.key.replace('_', ' ')}</strong>
                          {description && <> — {description}</>}
                        </span>
                      : 'Click a sign or press a key to begin')
                }
              </span>
              <button
                onClick={replay}
                disabled={!lastPlayed || !!playing}
                title='Replay last sign'
                style={{
                  background: 'none', border: 'none', cursor: lastPlayed && !playing ? 'pointer' : 'default',
                  color: lastPlayed && !playing ? '#7ec8e3' : '#444',
                  fontSize: '1rem', padding: '2px 6px',
                }}
              >
                <i className='fa fa-repeat' />
              </button>
            </div>

            <div id='canvas' />
          </div>

          {/* ── Right: controls ───────────────────────────────────────────── */}
          <div className='col-md-2'>
            <p className='bot-label'>Select Avatar</p>
            <img src={xbotPic} className='bot-image col-md-11' onClick={() => setBot(xbot)} alt='Avatar 1: XBOT' />
            <img src={ybotPic} className='bot-image col-md-11' onClick={() => setBot(ybot)} alt='Avatar 2: YBOT' />

            {/* Speed presets */}
            <p className='label-style' style={{ fontSize: '1rem', marginTop: 20, marginBottom: 6 }}>Speed Preset</p>
            <div className='d-flex' style={{ gap: 4 }}>
              {PRESETS.map(p => (
                <button
                  key={p.label}
                  onClick={() => applyPreset(p)}
                  style={{
                    flex: 1, padding: '5px 2px', borderRadius: 5,
                    fontSize: '0.72rem', fontWeight: 600, cursor: 'pointer',
                    background: preset === p.label ? '#4CAF50' : '#1e1e2e',
                    color: preset === p.label ? '#fff' : '#aaa',
                    border: preset === p.label ? '1px solid #4CAF50' : '1px solid #444',
                  }}
                >
                  {p.label}
                </button>
              ))}
            </div>

            <p className='label-style'>Animation Speed: {Math.round(speed * 100) / 100}</p>
            <Slider
              axis="x" xmin={0.05} xmax={1.0} xstep={0.01} x={speed}
              onChange={({ x }) => { setSpeed(x); setPreset(''); }}
              className='w-100'
            />
            <p className='label-style'>Pause time: {pause} ms</p>
            <Slider
              axis="x" xmin={0} xmax={2000} xstep={100} x={pause}
              onChange={({ x }) => { setPause(x); setPreset(''); }}
              className='w-100'
            />
          </div>

        </div>
      </div>
    </>
  );
}

export default LearnSign;
