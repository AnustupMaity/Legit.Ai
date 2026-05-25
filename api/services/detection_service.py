from __future__ import annotations

import time

from sqlalchemy.orm import Session

import config
from backend.model import fake_detection
from backend.model.audio_detector import detect_audio
from backend.model.document_processor import detect_document
from backend.model.fact_checker import initialize_knowledge_base, integrate_fact_check
from backend.model.url_fetcher import fetch_article_text
from backend.model.video_detector import detect_video
from db import crud
from schemas import DetectionResult
from utils.cache_key import content_hash
from utils.timeout import run_with_timeout


def apply_confidence_threshold(result: dict, threshold: float) -> dict:
    if threshold <= 0:
        return result
    if result.get("fake") and result.get("confidence", 0) < threshold:
        result = {**result}
        result["fake"] = False
        result["reason"] = (
            f"{result['reason']} (Not flagged: confidence {result['confidence']:.1f}% "
            f"is below your threshold of {threshold:.0f}%.)"
        )
    return result


def run_detection(
    db: Session,
    *,
    tenant_id: int | None = None,
    type_: str,
    content_for_hash: str | bytes,
    content_preview: str,
    run_fn,
    source: str | None = None,
    filename: str | None = None,
    confidence_threshold: float | None = None,
    skip_cache: bool = False,
) -> DetectionResult:
    threshold = (
        confidence_threshold
        if confidence_threshold is not None
        else crud.get_confidence_threshold(db)
    )
    h = content_hash(type_, content_for_hash)

    if config.CACHE_ENABLED and not skip_cache:
        cached_row = crud.get_cached_detection(db, h, config.CACHE_TTL_HOURS)
        if cached_row:
            return DetectionResult(
                id=cached_row.id,
                fake=cached_row.fake,
                confidence=cached_row.confidence,
                reason=f"[Cached] {cached_row.reason}",
                model=cached_row.model,
                labels=[],
                type=cached_row.type,
                content_preview=cached_row.content_preview,
                latency_ms=0.0,
                cached=True,
            )

    start = time.perf_counter()
    try:
        result = run_with_timeout(run_fn, config.ML_TIMEOUT_SECONDS)
    except TimeoutError as exc:
        raise TimeoutError(str(exc)) from exc

    result = apply_confidence_threshold(result, threshold)
    latency_ms = round((time.perf_counter() - start) * 1000, 1)
    row = crud.create_detection(
        db,
        tenant_id=tenant_id if tenant_id is not None else 0,
        type_=type_,
        content_preview=content_preview[:500],
        fake=result["fake"],
        confidence=result["confidence"],
        reason=result["reason"],
        model=result["model"],
        source=source,
        filename=filename,
        content_hash=h,
        latency_ms=latency_ms,
        cached=False,
        emotion=result.get("emotion"),
        emotion_confidence=result.get("emotion_confidence"),
    )
    return DetectionResult(
        id=row.id,
        fake=row.fake,
        confidence=row.confidence,
        reason=row.reason,
        model=row.model,
        labels=result.get("labels", []),
        type=type_,
        content_preview=row.content_preview,
        latency_ms=latency_ms,
        cached=False,
        emotion=row.emotion,
        emotion_confidence=row.emotion_confidence,
    )


def detect_text_content(
    db: Session,
    text: str,
    *,
    tenant_id: int | None = None,
    source: str | None = None,
    confidence_threshold: float | None = None,
    use_fact_checking: bool = True,
) -> DetectionResult:
    # Initialize knowledge base for fact checking
    if use_fact_checking:
        try:
            initialize_knowledge_base()
        except Exception as exc:
            print(f"Failed to initialize knowledge base: {exc}")
    
    def _run():
        result = fake_detection.detect(text, type_="text")
        # Integrate fact checking if enabled and available
        if use_fact_checking:
            try:
                result = integrate_fact_check(result, text)
            except Exception as exc:
                print(f"Fact checking failed: {exc}")
        return result
    
    return run_detection(
        db,
        tenant_id=tenant_id,
        type_="text",
        content_for_hash=text,
        content_preview=text,
        run_fn=_run,
        source=source,
        confidence_threshold=confidence_threshold,
    )


def detect_url_content(
    db: Session,
    url: str,
    *,
    tenant_id: int | None = None,
    confidence_threshold: float | None = None,
    use_fact_checking: bool = True,
) -> DetectionResult:
    # Initialize knowledge base for fact checking
    if use_fact_checking:
        try:
            initialize_knowledge_base()
        except Exception as exc:
            print(f"Failed to initialize knowledge base: {exc}")
    
    def _run():
        article = fetch_article_text(url, timeout=config.URL_FETCH_TIMEOUT_SECONDS)
        result = fake_detection.detect(article, type_="text")
        
        # Integrate fact checking if enabled
        if use_fact_checking:
            try:
                result = integrate_fact_check(result, article)
            except Exception as exc:
                print(f"Fact checking failed: {exc}")
        
        result["reason"] = f"From URL: {url[:80]}. {result['reason']}"
        result["labels"] = [{"label": "url", "score": 1.0}, *result.get("labels", [])]
        return result

    return run_detection(
        db,
        tenant_id=tenant_id,
        type_="url",
        content_for_hash=url,
        content_preview=url,
        run_fn=_run,
        source=url,
        confidence_threshold=confidence_threshold,
    )


def detect_image_content(
    db: Session,
    image_bytes: bytes,
    filename: str | None,
    *,
    tenant_id: int | None = None,
    confidence_threshold: float | None = None,
) -> DetectionResult:
    return run_detection(
        db,
        tenant_id=tenant_id,
        type_="image",
        content_for_hash=image_bytes,
        content_preview=filename or "uploaded-image",
        run_fn=lambda: fake_detection.detect(
            "",
            type_="image",
            image_bytes=image_bytes,
            filename=filename,
        ),
        filename=filename,
        confidence_threshold=confidence_threshold,
    )


def detect_audio_content(
    db: Session,
    audio_bytes: bytes,
    filename: str | None,
    *,
    tenant_id: int | None = None,
    confidence_threshold: float | None = None,
) -> DetectionResult:
    def _run():
        result = detect_audio(audio_bytes, filename)
        # Ensure the result has the expected format
        return {
            "fake": result.get("fake", False),
            "confidence": result.get("confidence", 50.0),
            "reason": result.get("reason", "Audio analysis completed"),
            "model": result.get("model", "audio-classifier"),
            "labels": result.get("labels", []),
            "emotion": result.get("emotion"),
            "emotion_confidence": result.get("emotion_confidence"),
        }
    
    return run_detection(
        db,
        tenant_id=tenant_id,
        type_="audio",
        content_for_hash=audio_bytes,
        content_preview=filename or "uploaded-audio",
        run_fn=_run,
        filename=filename,
        confidence_threshold=confidence_threshold,
    )


def detect_video_content(
    db: Session,
    video_bytes: bytes,
    filename: str | None,
    *,
    tenant_id: int | None = None,
    confidence_threshold: float | None = None,
) -> DetectionResult:
    def _run():
        result = detect_video(video_bytes, filename)
        # Ensure the result has the expected format
        return {
            "fake": result.get("fake", False),
            "confidence": result.get("confidence", 50.0),
            "reason": result.get("reason", "Video analysis completed"),
            "model": result.get("model", "video-processor"),
            "labels": result.get("labels", []),
        }
    
    return run_detection(
        db,
        tenant_id=tenant_id,
        type_="video",
        content_for_hash=video_bytes,
        content_preview=filename or "uploaded-video",
        run_fn=_run,
        filename=filename,
        confidence_threshold=confidence_threshold,
    )


def detect_document_content(
    db: Session,
    document_bytes: bytes,
    filename: str | None,
    *,
    tenant_id: int | None = None,
    confidence_threshold: float | None = None,
) -> DetectionResult:
    def _run():
        result = detect_document(document_bytes, filename, lambda text, type_: fake_detection.detect(text, type_=type_))
        # Ensure the result has the expected format
        return {
            "fake": result.get("fake", False),
            "confidence": result.get("confidence", 50.0),
            "reason": result.get("reason", "Document analysis completed"),
            "model": result.get("model", "document-processor"),
            "labels": result.get("labels", []),
        }
    
    return run_detection(
        db,
        tenant_id=tenant_id,
        type_="text",  # Documents are analyzed as text
        content_for_hash=document_bytes,
        content_preview=filename or "uploaded-document",
        run_fn=_run,
        filename=filename,
        confidence_threshold=confidence_threshold,
    )
