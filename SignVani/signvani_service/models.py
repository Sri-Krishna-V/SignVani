"""
SignVani Pydantic Models
Data structures for API requests and responses
"""
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field, validator


class AudioInput(BaseModel):
    """Audio input data"""
    sample_rate: int = Field(16000, description="Audio sample rate in Hz")
    channels: int = Field(1, description="Number of audio channels")
    duration: float = Field(...,
                            description="Duration in seconds", gt=0, le=60)


class TranscriptionResult(BaseModel):
    """Speech-to-text transcription result"""
    text: str = Field(..., description="Transcribed English text")
    confidence: float = Field(...,
                              description="Transcription confidence score", ge=0, le=1)
    alternatives: Optional[List[str]] = Field(
        None, description="Alternative transcriptions")
    processing_time: float = Field(...,
                                   description="Processing time in seconds")


class GlossResult(BaseModel):
    """NLP gloss generation result"""
    original_text: str = Field(..., description="Original English text")
    gloss: str = Field(..., description="ISL gloss representation")
    tokens: List[str] = Field(..., description="Gloss tokens")
    transformation_applied: bool = Field(
        ..., description="Whether SOV transformation was applied")
    processing_time: float = Field(...,
                                   description="Processing time in seconds")


class HamNoSysMapping(BaseModel):
    """HamNoSys mapping from database"""
    id: Optional[int] = None
    gloss_word: str = Field(..., description="ISL gloss word")
    hamnosys_xml: str = Field(...,
                              description="HamNoSys notation in XML format")
    english_word: Optional[str] = Field(
        None, description="Corresponding English word")
    confidence_score: float = Field(
        1.0, description="Mapping confidence", ge=0, le=1)
    region: Optional[str] = Field("Mumbai", description="Regional variant")
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SiGMLResult(BaseModel):
    """Visual synthesis SiGML result"""
    gloss: str = Field(..., description="ISL gloss input")
    sigml_xml: str = Field(..., description="Generated SiGML XML")
    hamnosys_mappings: List[HamNoSysMapping] = Field(
        ..., description="Retrieved HamNoSys mappings")
    missing_words: List[str] = Field(
        default_factory=list, description="Words not found in database")
    processing_time: float = Field(...,
                                   description="Processing time in seconds")


class ConversionProgress(BaseModel):
    """Real-time conversion progress (for SSE streaming)"""
    stage: str = Field(..., description="Current stage",
                       pattern="^(transcribing|generating_gloss|rendering_avatar|complete|error)$")
    progress: int = Field(..., description="Progress percentage", ge=0, le=100)
    message: Optional[str] = Field(None, description="Progress message")
    data: Optional[Dict] = Field(None, description="Stage-specific data")


class ConversionResult(BaseModel):
    """Complete speech-to-sign conversion result"""
    transcription: TranscriptionResult
    gloss: GlossResult
    sigml: SiGMLResult
    total_processing_time: float = Field(...,
                                         description="Total processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TextToSignRequest(BaseModel):
    """Request model for text-to-sign conversion"""
    text: str = Field(..., description="English text to convert",
                      min_length=1, max_length=500)
    region: Optional[str] = Field("Mumbai", description="ISL regional variant")
    enable_sov: bool = Field(
        True, description="Enable SVO to SOV transformation")

    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v.strip()


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    uptime: float = Field(..., description="Uptime in seconds")
    vosk_loaded: bool = Field(..., description="Whether Vosk model is loaded")
    spacy_loaded: bool = Field(...,
                               description="Whether spaCy model is loaded")
    database_connected: bool = Field(...,
                                     description="Whether database is accessible")
    gloss_mappings_count: int = Field(...,
                                      description="Number of gloss mappings in database")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict] = Field(
        None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GlossQueryResponse(BaseModel):
    """Response for gloss word query"""
    gloss_word: str
    found: bool
    hamnosys_mapping: Optional[HamNoSysMapping] = None
    suggestions: Optional[List[str]] = Field(
        None, description="Similar words if not found")


class DatabaseStats(BaseModel):
    """Database statistics"""
    total_mappings: int
    regions: List[str]
    most_common_words: List[Dict[str, int]]
    database_size_mb: float
    last_updated: Optional[datetime] = None
