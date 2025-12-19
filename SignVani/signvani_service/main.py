"""
SignVani Service - Main Application
FastAPI microservice for Offline Speech-to-Sign Language conversion
"""
import logging
import asyncio
import json
import time
from typing import AsyncGenerator

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from config import settings
from signvani_service.audio_processor import create_audio_processor
from signvani_service.nlp_pipeline import NLPPipeline
from signvani_service.visual_synthesizer import VisualSynthesizer
from signvani_service.database import DatabaseManager
from signvani_service.models import (
    ConversionProgress, ConversionResult, TextToSignRequest,
    HealthResponse, ErrorResponse
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("signvani")

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Offline Speech-to-Sign Language Conversion Service for Raspberry Pi"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components
audio_processor = None
nlp_pipeline = None
visual_synthesizer = None
db_manager = None


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global audio_processor, nlp_pipeline, visual_synthesizer, db_manager

    logger.info("Starting SignVani Service...")

    # 1. Initialize Database
    db_manager = DatabaseManager(str(settings.DATABASE_PATH))
    logger.info(f"Database initialized at {settings.DATABASE_PATH}")

    # 2. Initialize Audio Processor
    try:
        audio_processor = create_audio_processor(
            model_path=str(settings.VOSK_MODEL_PATH),
            mock=settings.MOCK_ASR,
            sample_rate=settings.AUDIO_SAMPLE_RATE
        )
    except Exception as e:
        logger.error(f"Failed to initialize Audio Processor: {e}")
        # Fallback to mock if model missing in dev
        if settings.DEBUG:
            logger.warning("Falling back to Mock Audio Processor")
            audio_processor = create_audio_processor(mock=True)

    # 3. Initialize NLP Pipeline
    try:
        nlp_pipeline = NLPPipeline(
            model_name=settings.SPACY_MODEL,
            enable_sov=settings.ENABLE_SOV_TRANSFORMATION
        )
    except Exception as e:
        logger.error(f"Failed to initialize NLP Pipeline: {e}")

    # 4. Initialize Visual Synthesizer
    visual_synthesizer = VisualSynthesizer(db_manager)

    logger.info("All components initialized")


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Service health check"""
    return HealthResponse(
        status="online",
        version=settings.APP_VERSION,
        uptime=time.process_time(),
        vosk_loaded=audio_processor is not None,
        spacy_loaded=nlp_pipeline is not None,
        database_connected=db_manager is not None,
        gloss_mappings_count=db_manager.get_stats(
        )['total_mappings'] if db_manager else 0
    )


@app.post("/api/convert-speech")
async def convert_speech(
    request: Request,
    audio: UploadFile = File(...)
):
    """
    Convert speech audio to Sign Language animation stream (SSE)
    """
    if not audio_processor or not nlp_pipeline:
        raise HTTPException(
            status_code=503, detail="Service components not initialized")

    # Read audio file
    audio_bytes = await audio.read()

    # Generator for SSE
    async def event_generator() -> AsyncGenerator[dict, None]:
        try:
            # Stage 1: Transcription
            yield {
                "event": "stage",
                "data": json.dumps(ConversionProgress(
                    stage="transcribing",
                    progress=10,
                    message="Processing audio..."
                ).model_dump())
            }

            # Simulate processing steps if using mock, or real processing
            # Note: Audio processing is blocking, so in a real async app we might want to run in threadpool
            # For Pi, simple sequential is fine for now

            text, confidence = audio_processor.transcribe_audio_file(
                audio_bytes)

            yield {
                "event": "stage",
                "data": json.dumps(ConversionProgress(
                    stage="transcribing",
                    progress=40,
                    message="Transcription complete",
                    data={"text": text, "confidence": confidence}
                ).model_dump())
            }

            # Stage 2: NLP (Gloss Generation)
            yield {
                "event": "stage",
                "data": json.dumps(ConversionProgress(
                    stage="generating_gloss",
                    progress=50,
                    message="Converting to ISL Gloss..."
                ).model_dump())
            }

            nlp_result = nlp_pipeline.process_text(text)

            yield {
                "event": "stage",
                "data": json.dumps(ConversionProgress(
                    stage="generating_gloss",
                    progress=70,
                    message="Gloss generated",
                    data=nlp_result
                ).model_dump())
            }

            # Stage 3: Visual Synthesis (SiGML)
            yield {
                "event": "stage",
                "data": json.dumps(ConversionProgress(
                    stage="rendering_avatar",
                    progress=80,
                    message="Generating avatar animation..."
                ).model_dump())
            }

            sigml_result = visual_synthesizer.generate_sigml(
                nlp_result['gloss'])

            yield {
                "event": "stage",
                "data": json.dumps(ConversionProgress(
                    stage="rendering_avatar",
                    progress=95,
                    message="Animation ready",
                    data={"missing_words": sigml_result['missing_words']}
                ).model_dump())
            }

            # Complete
            final_result = ConversionResult(
                transcription={"text": text, "confidence": confidence,
                               "processing_time": 0, "alternatives": []},  # TODO: pass real times
                gloss=nlp_result,
                sigml=sigml_result,
                total_processing_time=0  # TODO: calc total
            )

            yield {
                "event": "complete",
                # Send the SiGML result directly as data for the complete event
                "data": json.dumps(sigml_result)
            }

            # Log to DB
            db_manager.log_conversion(text, nlp_result['gloss'], 0)

        except Exception as e:
            logger.error(f"Conversion error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(event_generator())


@app.post("/api/text-to-sign")
async def text_to_sign(request: TextToSignRequest):
    """
    Convert text directly to Sign Language (bypass audio)
    """
    if not nlp_pipeline:
        raise HTTPException(
            status_code=503, detail="NLP pipeline not initialized")

    try:
        # NLP
        nlp_result = nlp_pipeline.process_text(request.text)

        # Visual Synthesis
        sigml_result = visual_synthesizer.generate_sigml(
            nlp_result['gloss'], request.region)

        return JSONResponse(content={
            "gloss": nlp_result,
            "sigml": sigml_result
        })

    except Exception as e:
        logger.error(f"Text conversion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
