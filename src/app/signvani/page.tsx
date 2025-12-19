"use client";

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Activity, Terminal, Wifi, WifiOff, Volume2 } from 'lucide-react';

export default function SignVaniPage() {
  const [isListening, setIsListening] = useState(false);
  const [status, setStatus] = useState<'idle' | 'recording' | 'processing' | 'playing'>('idle');
  const [transcript, setTranscript] = useState('');
  const [gloss, setGloss] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>();
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

  // Check backend health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/health');
        if (res.ok) setIsConnected(true);
      } catch (e) {
        setIsConnected(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  // Audio Visualizer
  useEffect(() => {
    if (!isListening || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      if (!analyserRef.current) return;
      
      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      analyserRef.current.getByteFrequencyData(dataArray);

      // Calculate average volume for UI
      const average = dataArray.reduce((a, b) => a + b) / bufferLength;
      setAudioLevel(average);

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const barWidth = (canvas.width / bufferLength) * 2.5;
      let barHeight;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        barHeight = dataArray[i] / 2;
        
        // Cyberpunk gradient
        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        gradient.addColorStop(0, '#00f3ff'); // Cyan
        gradient.addColorStop(1, '#bc13fe'); // Purple

        ctx.fillStyle = gradient;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

        x += barWidth + 1;
      }

      animationFrameRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [isListening]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Setup Audio Context for Visualizer
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
      sourceRef.current.connect(analyserRef.current);

      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await processAudio(audioBlob);
        
        // Cleanup audio context
        if (audioContextRef.current) {
          audioContextRef.current.close();
        }
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsListening(true);
      setStatus('recording');
      setTranscript('');
      setGloss('');
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Could not access microphone");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isListening) {
      mediaRecorderRef.current.stop();
      setIsListening(false);
      setStatus('processing');
    }
  };

  const processAudio = async (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append('audio', audioBlob);

    try {
      // Use EventSource for SSE
      // Since EventSource doesn't support POST with body easily, we might need a fetch wrapper or 
      // the backend to support GET with ID. 
      // However, the backend is implemented as POST /api/convert-speech.
      // Standard EventSource doesn't support POST.
      // We'll use fetch-event-source or just fetch and read the stream manually.
      
      const response = await fetch('http://localhost:8000/api/convert-speech', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Network response was not ok');
      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            const eventType = line.substring(7).trim();
            // The next line should be data:
            continue; // We need to parse the data line associated with this event
            // This simple parser is fragile. Let's use a library or robust parsing if needed.
            // But for now, let's just look for data: lines
          }
          
          if (line.startsWith('data: ')) {
            try {
              const dataStr = line.substring(6).trim();
              const data = JSON.parse(dataStr);
              
              // Handle different data structures based on event type (which we missed in simple parse)
              // But we can infer from content
              
              if (data.stage) {
                // Progress update
                if (data.stage === 'transcribing' && data.data?.text) {
                  setTranscript(data.data.text);
                }
                if (data.stage === 'generating_gloss' && data.data?.gloss) {
                  setGloss(data.data.gloss);
                }
                if (data.stage === 'rendering_avatar') {
                  setStatus('playing');
                }
              } else if (data.sigml_xml) {
                // Complete event
                console.log("Received SiGML", data.sigml_xml);
                if (iframeRef.current && iframeRef.current.contentWindow) {
                  iframeRef.current.contentWindow.postMessage({
                    type: 'SIGML',
                    xml: data.sigml_xml
                  }, '*');
                }
                setStatus('idle');
              }
            } catch (e) {
              console.error("Error parsing SSE data", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Error processing audio:", error);
      setStatus('idle');
    }
  };

  return (
    <div className="min-h-screen bg-black text-cyan-400 font-mono overflow-hidden selection:bg-cyan-900">
      {/* Background Grid Effect */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1a1a1a_1px,transparent_1px),linear-gradient(to_bottom,#1a1a1a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />

      {/* Header */}
      <header className="relative z-10 p-6 flex justify-between items-center border-b border-cyan-900/50 bg-black/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <Activity className="w-6 h-6 text-cyan-400 animate-pulse" />
          <h1 className="text-2xl font-bold tracking-wider bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
            SIGNVANI <span className="text-xs text-cyan-700 align-top">PRO</span>
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${isConnected ? 'border-green-500/50 bg-green-900/20' : 'border-red-500/50 bg-red-900/20'}`}>
            {isConnected ? <Wifi className="w-4 h-4 text-green-500" /> : <WifiOff className="w-4 h-4 text-red-500" />}
            <span className={`text-xs ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
              {isConnected ? 'SYSTEM ONLINE' : 'DISCONNECTED'}
            </span>
          </div>
        </div>
      </header>

      <main className="relative z-10 container mx-auto p-6 h-[calc(100vh-80px)] flex flex-col gap-6">
        
        {/* Avatar Display Area */}
        <div className="flex-1 relative rounded-2xl border border-cyan-900/50 bg-black/40 overflow-hidden shadow-[0_0_30px_rgba(0,243,255,0.1)]">
          <div className="absolute inset-0 flex items-center justify-center">
            <iframe 
              ref={iframeRef}
              src="/signvani-avatar/avatarnew.html"
              className="w-full h-full border-0"
              title="SignVani Avatar"
            />
          </div>
          
          {/* Overlay UI Elements */}
          <div className="absolute top-4 left-4 p-2 bg-black/60 backdrop-blur rounded border border-cyan-900/30">
            <div className="text-xs text-cyan-600 mb-1">MODE</div>
            <div className="text-sm font-bold text-cyan-300">REAL-TIME TRANSLATION</div>
          </div>
        </div>

        {/* Bottom Control Panel */}
        <div className="h-64 grid grid-cols-12 gap-6">
          
          {/* Visualizer & Controls */}
          <div className="col-span-4 bg-black/40 border border-cyan-900/50 rounded-xl p-4 flex flex-col justify-between relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-t from-cyan-900/10 to-transparent pointer-events-none" />
            
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-2 text-cyan-500">
                <Volume2 className="w-4 h-4" />
                <span className="text-xs tracking-widest">AUDIO INPUT</span>
              </div>
              <div className="text-xs text-cyan-700">{status.toUpperCase()}</div>
            </div>

            <canvas 
              ref={canvasRef} 
              width="300" 
              height="100" 
              className="w-full h-24 opacity-80"
            />

            <button
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onTouchStart={startRecording}
              onTouchEnd={stopRecording}
              className={`w-full mt-4 py-4 rounded-lg font-bold tracking-widest transition-all duration-200 flex items-center justify-center gap-3
                ${isListening 
                  ? 'bg-red-500/20 border border-red-500 text-red-400 shadow-[0_0_20px_rgba(239,68,68,0.4)]' 
                  : 'bg-cyan-500/10 border border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/20 hover:shadow-[0_0_20px_rgba(6,182,212,0.2)]'
                }`}
            >
              {isListening ? (
                <>
                  <Mic className="w-5 h-5 animate-pulse" />
                  LISTENING...
                </>
              ) : (
                <>
                  <MicOff className="w-5 h-5" />
                  HOLD TO SPEAK
                </>
              )}
            </button>
          </div>

          {/* Transcript & Gloss Display */}
          <div className="col-span-8 bg-black/40 border border-cyan-900/50 rounded-xl p-6 flex flex-col gap-4 relative">
            
            {/* English Transcript */}
            <div className="flex-1">
              <div className="flex items-center gap-2 text-purple-400 mb-2">
                <Terminal className="w-4 h-4" />
                <span className="text-xs tracking-widest">TRANSCRIPT</span>
              </div>
              <div className="text-xl text-white/90 font-light min-h-[2rem]">
                {transcript || <span className="text-white/20 italic">Waiting for speech...</span>}
              </div>
            </div>

            <div className="h-px bg-gradient-to-r from-transparent via-cyan-900/50 to-transparent" />

            {/* ISL Gloss */}
            <div className="flex-1">
              <div className="flex items-center gap-2 text-cyan-400 mb-2">
                <Activity className="w-4 h-4" />
                <span className="text-xs tracking-widest">ISL GLOSS</span>
              </div>
              <div className="text-2xl text-cyan-300 font-bold tracking-wide min-h-[2rem]">
                {gloss || <span className="text-cyan-900/40">---</span>}
              </div>
            </div>

          </div>
        </div>
      </main>
    </div>
  );
}
