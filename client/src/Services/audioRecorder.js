/**
 * Enhanced Audio Recorder for SignVani
 * Records audio and sends to backend for processing
 */

class AudioRecorder {
  constructor() {
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.stream = null;
    this.isRecording = false;
    this.onTranscript = null;
    this.onError = null;
    this.onProcessingStart = null;
    this.onProcessingEnd = null;
  }

  /**
   * Initialize audio recorder
   * @param {Object} options - Configuration options
   */
  async initialize(options = {}) {
    try {
      this.onTranscript = options.onTranscript;
      this.onError = options.onError;
      this.onProcessingStart = options.onProcessingStart;
      this.onProcessingEnd = options.onProcessingEnd;

      // Request microphone access
      this.stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
          channelCount: 1
        } 
      });

      // Create media recorder
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      // Setup event handlers
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = async () => {
        await this.processAudio();
      };

      console.log('Audio recorder initialized successfully');
      return true;
    } catch (error) {
      console.error('Failed to initialize audio recorder:', error);
      if (this.onError) {
        this.onError('Failed to access microphone. Please check permissions.');
      }
      return false;
    }
  }

  /**
   * Start recording
   */
  startRecording() {
    if (!this.mediaRecorder) {
      if (this.onError) {
        this.onError('Audio recorder not initialized');
      }
      return;
    }

    if (this.isRecording) {
      console.warn('Recording already in progress');
      return;
    }

    this.audioChunks = [];
    this.mediaRecorder.start();
    this.isRecording = true;
    console.log('Recording started');
  }

  /**
   * Stop recording
   */
  stopRecording() {
    if (!this.isRecording) {
      console.warn('No recording in progress');
      return;
    }

    this.mediaRecorder.stop();
    this.isRecording = false;
    console.log('Recording stopped');
  }

  /**
   * Process recorded audio and send to backend
   */
  async processAudio() {
    if (this.audioChunks.length === 0) {
      console.warn('No audio data to process');
      return;
    }

    try {
      if (this.onProcessingStart) {
        this.onProcessingStart();
      }

      // Create audio blob
      const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
      
      // Convert to WAV format for backend compatibility
      const wavBlob = await this.convertToWav(audioBlob);
      
      // Send to backend
      const apiService = (await import('./apiService')).default;
      const result = await apiService.speechToSign(wavBlob);

      if (this.onTranscript) {
        this.onTranscript(result);
      }

    } catch (error) {
      console.error('Error processing audio:', error);
      if (this.onError) {
        this.onError('Failed to process audio. Please try again.');
      }
    } finally {
      if (this.onProcessingEnd) {
        this.onProcessingEnd();
      }
    }
  }

  /**
   * Convert WebM/Opus blob to 16-bit mono WAV using the Web Audio API.
   * The Vosk ASR engine on the backend requires standard WAV (PCM) input.
   * @param {Blob} audioBlob - Recorded audio blob (WebM or other browser format)
   * @returns {Promise<Blob>} - 16-bit mono WAV blob at the original sample rate
   */
  async convertToWav(audioBlob) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) {
      console.warn('Web Audio API not supported; sending raw audio to backend');
      return audioBlob;
    }

    const audioContext = new AudioContext();
    try {
      const arrayBuffer = await audioBlob.arrayBuffer();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

      // Mix down to mono by averaging all channels
      const numChannels = audioBuffer.numberOfChannels;
      const numSamples = audioBuffer.length;
      const sampleRate = audioBuffer.sampleRate;
      const monoSamples = new Float32Array(numSamples);

      for (let ch = 0; ch < numChannels; ch++) {
        const channelData = audioBuffer.getChannelData(ch);
        for (let i = 0; i < numSamples; i++) {
          monoSamples[i] += channelData[i];
        }
      }
      if (numChannels > 1) {
        for (let i = 0; i < numSamples; i++) {
          monoSamples[i] /= numChannels;
        }
      }

      // Encode as 16-bit PCM WAV
      const bitDepth = 16;
      const bytesPerSample = bitDepth / 8;
      const dataLength = numSamples * bytesPerSample;
      const wavBuffer = new ArrayBuffer(44 + dataLength);
      const view = new DataView(wavBuffer);

      const writeString = (offset, str) => {
        for (let i = 0; i < str.length; i++) {
          view.setUint8(offset + i, str.charCodeAt(i));
        }
      };

      // RIFF header
      writeString(0, 'RIFF');
      view.setUint32(4, 36 + dataLength, true);
      writeString(8, 'WAVE');
      // fmt  chunk
      writeString(12, 'fmt ');
      view.setUint32(16, 16, true);          // chunk size
      view.setUint16(20, 1, true);           // PCM format
      view.setUint16(22, 1, true);           // mono
      view.setUint32(24, sampleRate, true);
      view.setUint32(28, sampleRate * bytesPerSample, true); // byte rate
      view.setUint16(32, bytesPerSample, true);              // block align
      view.setUint16(34, bitDepth, true);
      // data chunk
      writeString(36, 'data');
      view.setUint32(40, dataLength, true);

      // Write 16-bit PCM samples
      let offset = 44;
      for (let i = 0; i < numSamples; i++, offset += 2) {
        const clamped = Math.max(-1, Math.min(1, monoSamples[i]));
        view.setInt16(offset, clamped < 0 ? clamped * 0x8000 : clamped * 0x7FFF, true);
      }

      return new Blob([wavBuffer], { type: 'audio/wav' });
    } finally {
      audioContext.close();
    }
  }

  /**
   * Clean up resources
   */
  cleanup() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.isRecording = false;
  }

  /**
   * Check if recording is in progress
   */
  isCurrentlyRecording() {
    return this.isRecording;
  }
}

export default AudioRecorder;
