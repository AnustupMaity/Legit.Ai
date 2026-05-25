from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TextDetectionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    source: str | None = None
    confidence_threshold: float | None = Field(None, ge=0, le=100)


class UrlDetectionRequest(BaseModel):
    url: str = Field(..., min_length=10, max_length=2048)
    confidence_threshold: float | None = Field(None, ge=0, le=100)


class BatchTextRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=20)
    source: str | None = None
    confidence_threshold: float | None = Field(None, ge=0, le=100)


class AppSettings(BaseModel):
    confidence_threshold: float = Field(50, ge=0, le=100)
    use_llm: bool | None = None


class DetectionResult(BaseModel):
    id: int | None = None
    fake: bool
    confidence: float = Field(..., ge=0, le=100)
    reason: str
    model: str
    labels: list[dict] = Field(default_factory=list)
    type: Literal["text", "image", "url", "audio", "video", "document"] = "text"
    content_preview: str | None = None
    latency_ms: float | None = None
    cached: bool = False
    emotion: str | None = None  # For audio analysis
    emotion_confidence: float | None = None  # For audio analysis


class BatchDetectionResponse(BaseModel):
    results: list[DetectionResult]
    total: int


class DetectionRecord(BaseModel):
    id: int
    type: str
    content_preview: str
    fake: bool
    confidence: float
    reason: str
    model: str
    source: str | None
    filename: str | None
    latency_ms: float | None = None
    cached: bool = False
    emotion: str | None = None
    emotion_confidence: float | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    items: list[DetectionRecord]
    total: int


class StatsResponse(BaseModel):
    scanned_today: int
    threats_total: int
    threats_today: int
    fake_rate_percent: float
    recent_count: int
    by_type: dict[str, int]
    cache_hits: int = 0


class HealthResponse(BaseModel):
    status: str
    text_model_loaded: bool
    image_model_loaded: bool
    image_ai_model_loaded: bool
    enhanced_text_model_loaded: bool
    audio_model_loaded: bool
    zero_shot_model_loaded: bool
    gemini_configured: bool
    use_llm: bool
    cache_enabled: bool
    rate_limit_per_minute: int
