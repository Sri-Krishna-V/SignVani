/**
 * API Service for SignVani Frontend
 * Handles communication with the NLP backend
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  /**
   * Check backend health
   */
  async healthCheck() {
    try {
      const response = await fetch(`${this.baseURL}/api/health`);
      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }

  /**
   * Convert text to sign language
   * @param {string} text - Input text to convert
   * @returns {Promise<Object>} - Conversion result with gloss and HamNoSys codes
   */
  async textToSign(text) {
    try {
      const response = await fetch(`${this.baseURL}/api/text-to-sign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Text to sign conversion failed:', error);
      throw error;
    }
  }

  /**
   * Convert speech audio to sign language
   * @param {Blob} audioBlob - Audio data as blob
   * @returns {Promise<Object>} - Conversion result with transcript, gloss and HamNoSys codes
   */
  async speechToSign(audioBlob) {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'speech.wav');

      const response = await fetch(`${this.baseURL}/api/speech-to-sign`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Speech to sign conversion failed:', error);
      throw error;
    }
  }

  /**
   * Create WebSocket connection for real-time speech processing
   * @param {Function} onMessage - Callback for received messages
   * @param {Function} onError - Callback for errors
   * @param {Function} onClose - Callback for connection close
   * @returns {WebSocket} - WebSocket connection
   */
  createLiveSpeechConnection(onMessage, onError, onClose) {
    try {
      const wsUrl = `${this.baseURL.replace('http', 'ws')}/ws/live-speech`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connection established');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (onError) onError(error);
      };

      ws.onclose = () => {
        console.log('WebSocket connection closed');
        if (onClose) onClose();
      };

      return ws;
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      throw error;
    }
  }

  /**
   * Send audio chunk through WebSocket
   * @param {WebSocket} ws - WebSocket connection
   * @param {Blob} audioChunk - Audio chunk to send
   */
  sendAudioChunk(ws, audioChunk) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(audioChunk);
    } else {
      console.warn('WebSocket is not ready for sending data');
    }
  }
}

export default new ApiService();
