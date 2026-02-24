"""
FastAPI Wrapper for SignVani Backend
Provides HTTP endpoints for the NLP pipeline to communicate with frontend
"""

from src.asr.vosk_integration import get_asr_engine, convert_to_wav
from src.nlp.dataclasses import GlossPhrase, SiGMLOutput
from src.sigml.generator import SiGMLGenerator
from src.nlp.gloss_mapper import GlossMapper
from src.pipeline.orchestrator import PipelineOrchestrator
from src.database.seed_db import seed_database
import asyncio
import logging
import io
import wave
import json
import sys
from typing import Optional, Dict, Any
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SignVani API",
    description="Speech to Indian Sign Language Translation API",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components (initialized once)
gloss_mapper: Optional[GlossMapper] = None
sigml_generator: Optional[SiGMLGenerator] = None
pipeline_orchestrator: Optional[PipelineOrchestrator] = None

# WebSocket connection manager


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.on_event("startup")
async def startup_event():
    """Initialize NLP components on startup"""
    global gloss_mapper, sigml_generator, pipeline_orchestrator

    logger.info("Initializing SignVani API...")

    try:
        # Seed the gloss database (INSERT OR IGNORE — safe to call on every startup)
        logger.info("Seeding ISL gloss database...")
        seed_database(force_update=False)
        logger.info("Database seeded.")

        # Initialize NLP components
        logger.info("Loading NLP models...")
        gloss_mapper = GlossMapper(prewarm=True)
        sigml_generator = SiGMLGenerator()

        # Initialize pipeline orchestrator (optional, for real-time processing)
        # pipeline_orchestrator = PipelineOrchestrator(avatar_enabled=False)

        logger.info("SignVani API ready!")

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ready",
        "message": "SignVani API is running",
        "components": {
            "gloss_mapper": gloss_mapper is not None,
            "sigml_generator": sigml_generator is not None,
            "pipeline_orchestrator": pipeline_orchestrator is not None
        }
    }


@app.post("/api/text-to-sign")
async def text_to_sign(request: Dict[str, str]):
    """
    Convert text directly to sign language HamNoSys codes

    Args:
        request: {"text": "Hello world"}

    Returns:
        {"original_text": "Hello world", "gloss": "HELLO WORLD", "hamnosys": "...", "sigml": "..."}
    """
    if not gloss_mapper or not sigml_generator:
        raise HTTPException(
            status_code=503, detail="NLP components not initialized")

    text = request.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    try:
        # Process text through NLP pipeline
        logger.info(f"Processing text: '{text}'")

        # SVO to SOV conversion and gloss mapping
        gloss_phrase: GlossPhrase = gloss_mapper.process(text)

        # Generate HamNoSys/SiGML codes
        sigml_output: SiGMLOutput = sigml_generator.generate(gloss_phrase)

        response = {
            "original_text": text,
            "gloss": gloss_phrase.gloss_string,
            "glosses": gloss_phrase.glosses,
            "tense": gloss_phrase.tense,
            "is_negated": gloss_phrase.is_negated,
            "question_type": gloss_phrase.question_type,
            "hamnosys": sigml_output.hamnosys_codes if hasattr(sigml_output, 'hamnosys_codes') else [],
            "sigml": sigml_output.sigml_xml,
            "processing_time_ms": sigml_output.processing_time_ms if hasattr(sigml_output, 'processing_time_ms') else 0
        }

        logger.info(
            f"Successfully processed: '{text}' -> '{gloss_phrase.gloss_string}' "
            f"| tense={gloss_phrase.tense} | is_negated={gloss_phrase.is_negated} "
            f"| question_type={gloss_phrase.question_type}")
        return response

    except Exception as e:
        logger.error(f"Error processing text '{text}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/api/speech-to-sign")
async def speech_to_sign(audio: UploadFile = File(...)):
    """
    Convert speech audio to sign language HamNoSys codes

    Args:
        audio: Audio file (WAV, MP3, etc.)

    Returns:
        Same format as /api/text-to-sign but with ASR transcript
    """
    if not gloss_mapper or not sigml_generator:
        raise HTTPException(
            status_code=503, detail="NLP components not initialized")

    try:
        # Read and process audio file
        audio_content = await audio.read()

        # Convert audio to WAV format if needed
        audio_data = await process_audio_file(audio_content, audio.content_type)

        # For now, we'll use a placeholder ASR. In a real implementation,
        # you would integrate with Vosk or another ASR engine
        transcript = await transcribe_audio(audio_data)

        if not transcript:
            raise HTTPException(
                status_code=400, detail="Could not transcribe audio")

        # Process transcript through NLP pipeline
        logger.info(f"Processing transcript: '{transcript}'")

        gloss_phrase: GlossPhrase = gloss_mapper.process(transcript)
        sigml_output: SiGMLOutput = sigml_generator.generate(gloss_phrase)

        response = {
            "original_text": transcript,
            "gloss": gloss_phrase.gloss_string,
            "glosses": gloss_phrase.glosses,
            "tense": gloss_phrase.tense,
            "is_negated": gloss_phrase.is_negated,
            "question_type": gloss_phrase.question_type,
            "hamnosys": sigml_output.hamnosys_codes if hasattr(sigml_output, 'hamnosys_codes') else [],
            "sigml": sigml_output.sigml_xml,
            "processing_time_ms": sigml_output.processing_time_ms if hasattr(sigml_output, 'processing_time_ms') else 0
        }

        logger.info(
            f"Successfully processed audio: '{transcript}' -> '{gloss_phrase.gloss_string}' "
            f"| tense={gloss_phrase.tense} | is_negated={gloss_phrase.is_negated} "
            f"| question_type={gloss_phrase.question_type}")
        return response

    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        raise HTTPException(
            status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/api/text-to-handsign")
async def text_to_handsign(request: Dict[str, str]):
    """
    Convert text directly to frontend-compatible hand sign animations

    This endpoint bypasses SiGML XML generation and creates animations
    that can be directly consumed by the frontend 3D avatar system.

    Args:
        request: {"text": "Hello world"}

    Returns:
        {
            "original_text": "Hello world",
            "gloss": "HELLO WORLD",
            "total_duration": 2500,
            "animations": [
                {
                    "gloss": "HELLO",
                    "hamnosys": "hamflathand,hampalmu,hamchin,hammoveo,hammoved",
                    "duration": 1200,
                    "keyframes": [...]
                },
                ...
            ]
        }
    """
    if not gloss_mapper or not sigml_generator:
        raise HTTPException(
            status_code=503, detail="NLP components not initialized")

    text = request.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    try:
        # Process text through NLP pipeline
        logger.info(f"Processing text for hand signs: '{text}'")

        # SVO to SOV conversion and gloss mapping
        gloss_phrase: GlossPhrase = gloss_mapper.process(text)

        # Generate hand sign animations directly from NLP pipeline output
        handsign_animations = sigml_generator.generate_handsign_animations(
            gloss_phrase)

        response = {
            "original_text": text,
            "gloss": gloss_phrase.gloss_string,
            "glosses": gloss_phrase.glosses,
            "tense": gloss_phrase.tense,
            "is_negated": gloss_phrase.is_negated,
            "question_type": gloss_phrase.question_type,
            **handsign_animations  # Include all animation data
        }

        logger.info(
            f"Successfully generated hand signs: '{text}' -> {len(handsign_animations.get('animations', []))} animations "
            f"| tense={gloss_phrase.tense} | is_negated={gloss_phrase.is_negated} "
            f"| question_type={gloss_phrase.question_type}")
        return response

    except Exception as e:
        logger.error(f"Error generating hand signs for text '{text}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Animation generation failed: {str(e)}")


@app.post("/api/speech-to-handsign")
async def speech_to_handsign(audio: UploadFile = File(...)):
    """
    Convert speech audio directly to frontend-compatible hand sign animations

    Args:
        audio: Audio file (WAV, MP3, etc.)

    Returns:
        Same format as /api/text-to-handsign but with ASR transcript
    """
    if not gloss_mapper or not sigml_generator:
        raise HTTPException(
            status_code=503, detail="NLP components not initialized")

    try:
        # Read and process audio file
        audio_content = await audio.read()

        # Convert audio to WAV format if needed
        audio_data = await process_audio_file(audio_content, audio.content_type)

        # Transcribe audio
        transcript = await transcribe_audio(audio_data)

        if not transcript:
            raise HTTPException(
                status_code=400, detail="Could not transcribe audio")

        # Process transcript through NLP pipeline
        logger.info(f"Processing transcript for hand signs: '{transcript}'")

        gloss_phrase: GlossPhrase = gloss_mapper.process(transcript)
        handsign_animations = sigml_generator.generate_handsign_animations(
            gloss_phrase)

        response = {
            "original_text": transcript,
            "gloss": gloss_phrase.gloss_string,
            "glosses": gloss_phrase.glosses,
            "tense": gloss_phrase.tense,
            "is_negated": gloss_phrase.is_negated,
            "question_type": gloss_phrase.question_type,
            **handsign_animations  # Include all animation data
        }

        logger.info(
            f"Successfully generated hand signs from speech: '{transcript}' -> {len(handsign_animations.get('animations', []))} animations "
            f"| tense={gloss_phrase.tense} | is_negated={gloss_phrase.is_negated} "
            f"| question_type={gloss_phrase.question_type}")
        return response

    except Exception as e:
        logger.error(f"Error generating hand signs from audio: {e}")
        raise HTTPException(
            status_code=500, detail=f"Animation generation failed: {str(e)}")


@app.websocket("/ws/live-speech")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time speech processing
    """
    await manager.connect(websocket)
    try:
        while True:
            # Receive audio data from frontend
            data = await websocket.receive_bytes()

            # Process audio chunk
            try:
                # This would integrate with your Vosk streaming ASR
                # For now, we'll send a placeholder response
                response = {
                    "type": "processing",
                    "message": "Processing audio chunk..."
                }
                await manager.send_personal_message(json.dumps(response), websocket)

            except Exception as e:
                error_response = {
                    "type": "error",
                    "message": f"Processing error: {str(e)}"
                }
                await manager.send_personal_message(json.dumps(error_response), websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def process_audio_file(audio_content: bytes, content_type: str) -> bytes:
    """
    Convert audio file to WAV format for processing

    Args:
        audio_content: Raw audio bytes
        content_type: MIME type of audio

    Returns:
        WAV format audio bytes
    """
    # For now, assume input is already WAV
    # In a real implementation, you'd use ffmpeg or similar to convert
    return audio_content


async def transcribe_audio(audio_data: bytes) -> str:
    """
    Transcribe audio using ASR engine

    Args:
        audio_data: WAV format audio bytes

    Returns:
        Transcribed text
    """
    try:
        # Get ASR engine
        asr = get_asr_engine()

        # Convert to WAV format if needed
        wav_data = convert_to_wav(audio_data)

        # Transcribe
        transcript = asr.transcribe_audio_file(wav_data)

        logger.info(f"ASR transcript: '{transcript}'")
        return transcript

    except Exception as e:
        logger.error(f"ASR transcription error: {e}")
        return ""


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "components": {
            "gloss_mapper": gloss_mapper is not None,
            "sigml_generator": sigml_generator is not None,
            "pipeline_orchestrator": pipeline_orchestrator is not None,
            "handsign_generator": sigml_generator.handsign_generator is not None if sigml_generator else False
        },
        "endpoints": {
            "text_to_sign": "/api/text-to-sign",
            "speech_to_sign": "/api/speech-to-sign",
            "text_to_handsign": "/api/text-to-handsign",
            "speech_to_handsign": "/api/speech-to-handsign",
            "live_speech": "/ws/live-speech"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
