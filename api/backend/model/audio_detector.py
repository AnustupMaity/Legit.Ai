from __future__ import annotations

import io
import tempfile

import config
import torch
from transformers import pipeline

_audio_pipeline = None
_emotion_pipeline = None
_load_error: str | None = None


def load_audio_model() -> bool:
    global _audio_pipeline, _load_error
    if _audio_pipeline is not None:
        return True
    try:
        kwargs = {"model": config.MODEL_AUDIO}
        if config.HF_TOKEN:
            kwargs["token"] = config.HF_TOKEN
        _audio_pipeline = pipeline(
            "audio-classification",
            device=config.DEVICE,
            **kwargs,
        )
        _load_error = None
        return True
    except Exception as exc:
        _load_error = str(exc)
        _audio_pipeline = None
        return False


def load_emotion_model() -> bool:
    global _emotion_pipeline
    if _emotion_pipeline is not None:
        return True
    try:
        # Load Silero for emotion detection
        kwargs = {"model": "huggingface/speechbrain-emotion-recognition"}
        if config.HF_TOKEN:
            kwargs["token"] = config.HF_TOKEN
        _emotion_pipeline = pipeline("audio-classification", device=config.DEVICE, **kwargs)
        return True
    except Exception as exc:
        print(f"Emotion model load failed: {exc}")
        _emotion_pipeline = None
        return False


def is_audio_model_loaded() -> bool:
    return _audio_pipeline is not None


def get_audio_load_error() -> str | None:
    return _load_error


def _classify_audio(audio_bytes: bytes) -> tuple[bool, float, str, list[dict]]:
    """Classify audio for AI-generated/deepfake content."""
    if not load_audio_model() or _audio_pipeline is None:
        return False, 0.0, "Audio model unavailable.", []

    try:
        # Save bytes to temp file for pipeline
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_bytes)
            temp_file.flush()
            temp_path = temp_file.name

        # Run classification
        outputs = _audio_pipeline(temp_path)
        
        # Clean up temp file
        import os
        try:
            os.unlink(temp_path)
        except:
            pass

        if not outputs:
            return False, 0.0, "No classification results.", []

        top = outputs[0] if isinstance(outputs, list) else outputs
        label = str(top.get("label", ""))
        score = float(top.get("score", 0.0))
        
        # Check for AI-related labels
        fake_indicators = ["synthetic", "artificial", "ai", "generated", "deepfake", "tts"]
        is_fake = any(indicator in label.lower() for indicator in fake_indicators)
        
        labels = [
            {"label": str(r.get("label", "")), "score": float(r.get("score", 0.0))}
            for r in (outputs if isinstance(outputs, list) else [outputs])
        ]
        
        confidence = round(score * 100, 1)
        reason = f"Audio classification: '{label}' ({confidence}%)"
        
        return is_fake, confidence, reason, labels

    except Exception as exc:
        return False, 0.0, f"Audio classification failed: {str(exc)}", []


def _detect_emotion(audio_bytes: bytes) -> dict:
    """Detect emotion in audio using Silero."""
    if not load_emotion_model() or _emotion_pipeline is None:
        return {"emotion": "unknown", "confidence": 0.0}

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_bytes)
            temp_file.flush()
            temp_path = temp_file.name

        outputs = _emotion_pipeline(temp_path)
        
        import os
        try:
            os.unlink(temp_path)
        except:
            pass

        if outputs:
            top = outputs[0] if isinstance(outputs, list) else outputs
            return {
                "emotion": str(top.get("label", "unknown")),
                "confidence": float(top.get("score", 0.0))
            }
    except Exception as exc:
        print(f"Emotion detection failed: {exc}")

    return {"emotion": "unknown", "confidence": 0.0}


def detect_audio(audio_bytes: bytes, filename: str | None = None) -> dict:
    """Main audio detection function combining classification and emotion analysis."""
    fake, confidence, reason, labels = _classify_audio(audio_bytes)
    emotion_result = _detect_emotion(audio_bytes)
    
    result = {
        "fake": fake,
        "confidence": confidence or 50.0,
        "reason": reason,
        "model": config.MODEL_AUDIO,
        "labels": labels,
        "emotion": emotion_result.get("emotion", "unknown"),
        "emotion_confidence": emotion_result.get("confidence", 0.0),
    }
    
    if filename:
        result["labels"] = [{"label": "audio", "score": 1.0}, *result.get("labels", [])]

    return result
