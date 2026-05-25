from __future__ import annotations

import time
from typing import Any

from celery import Task

from backend.model import fake_detection
from celery_app import celery_app


class MLTask(Task):
    """Base class for ML tasks with error handling and timeout management."""
    
    _model_loaded = False
    
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        # Load models if not already loaded
        if not self._model_loaded:
            fake_detection.preload_models()
            self._model_loaded = True
        
        return super().__call__(*args, **kwargs)


@celery_app.task(
    bind=True,
    base=MLTask,
    name="detect_text_async",
    max_retries=2,
    default_retry_delay=60
)
def detect_text_async(self, text: str, source: str | None = None) -> dict:
    """
    Asynchronously detect fake news in text.
    
    Args:
        text: Text content to analyze
        source: Source of the text (optional)
    
    Returns:
        Detection result dictionary
    """
    try:
        start_time = time.time()
        result = fake_detection.detect(text, type_="text")
        result["latency_ms"] = (time.time() - start_time) * 1000
        result["source"] = source
        result["task_id"] = self.request.id
        return result
    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    base=MLTask,
    name="detect_image_async",
    max_retries=2,
    default_retry_delay=60
)
def detect_image_async(self, image_bytes: bytes, filename: str | None = None) -> dict:
    """
    Asynchronously detect AI-generated images.
    
    Args:
        image_bytes: Image file content
        filename: Original filename
    
    Returns:
        Detection result dictionary
    """
    try:
        start_time = time.time()
        result = fake_detection.detect("", type_="image", image_bytes=image_bytes, filename=filename)
        result["latency_ms"] = (time.time() - start_time) * 1000
        result["filename"] = filename
        result["task_id"] = self.request.id
        return result
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    base=MLTask,
    name="detect_audio_async",
    max_retries=2,
    default_retry_delay=60
)
def detect_audio_async(self, audio_bytes: bytes, filename: str | None = None) -> dict:
    """
    Asynchronously detect AI-generated audio.
    
    Args:
        audio_bytes: Audio file content
        filename: Original filename
    
    Returns:
        Detection result dictionary
    """
    try:
        from backend.model.audio_detector import detect_audio
        
        start_time = time.time()
        result = detect_audio(audio_bytes, filename)
        result["latency_ms"] = (time.time() - start_time) * 1000
        result["filename"] = filename
        result["task_id"] = self.request.id
        return result
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    base=MLTask,
    name="detect_video_async",
    max_retries=1,
    default_retry_delay=120
)
def detect_video_async(self, video_bytes: bytes, filename: str | None = None) -> dict:
    """
    Asynchronously detect AI-generated video content.
    
    Args:
        video_bytes: Video file content
        filename: Original filename
    
    Returns:
        Detection result dictionary
    """
    try:
        from backend.model.video_detector import detect_video
        
        start_time = time.time()
        result = detect_video(video_bytes, filename)
        result["latency_ms"] = (time.time() - start_time) * 1000
        result["filename"] = filename
        result["task_id"] = self.request.id
        return result
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    base=MLTask,
    name="detect_batch_async",
    max_retries=2,
    default_retry_delay=60
)
def detect_batch_async(self, texts: list[str], source: str | None = None) -> list[dict]:
    """
    Asynchronously detect fake news in multiple texts.
    
    Args:
        texts: List of texts to analyze
        source: Source of the texts (optional)
    
    Returns:
        List of detection result dictionaries
    """
    try:
        results = []
        for i, text in enumerate(texts):
            start_time = time.time()
            result = fake_detection.detect(text, type_="text")
            result["latency_ms"] = (time.time() - start_time) * 1000
            result["source"] = source or f"batch-{i+1}"
            result["task_id"] = self.request.id
            results.append(result)
        return results
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(name="preload_models")
def preload_models_task() -> dict:
    """
    Preload ML models into memory.
    This task should be called when the worker starts.
    """
    try:
        fake_detection.preload_models()
        return {"status": "success", "message": "Models loaded successfully"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
