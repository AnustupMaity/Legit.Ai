from __future__ import annotations

import io

from PIL import Image

import config
from backend.model.text_detector import _label_is_fake, detect_text

_caption_pipeline = None
_ai_image_pipeline = None
_load_error: str | None = None
_ai_load_error: str | None = None


def load_image_model() -> bool:
    global _caption_pipeline, _load_error
    if _caption_pipeline is not None:
        return True
    try:
        from transformers import pipeline

        kwargs = {"model": config.MODEL_IMAGE_CAPTION}
        _caption_pipeline = pipeline("image-to-text", device=-1, **kwargs)
        _load_error = None
        return True
    except Exception as exc:
        _load_error = str(exc)
        _caption_pipeline = None
        return False


def load_ai_image_classifier() -> bool:
    global _ai_image_pipeline, _ai_load_error
    if not config.USE_IMAGE_AI_CLASSIFIER:
        return False
    if _ai_image_pipeline is not None:
        return True
    try:
        from transformers import pipeline

        kwargs = {"model": config.MODEL_IMAGE_AI}
        _ai_image_pipeline = pipeline("image-classification", device=-1, **kwargs)
        _ai_load_error = None
        return True
    except Exception as exc:
        _ai_load_error = str(exc)
        _ai_image_pipeline = None
        # Fallback to original model if enhanced model fails
        try:
            kwargs["model"] = "umm-maybe/AI-image-detector"
            _ai_image_pipeline = pipeline("image-classification", device=-1, **kwargs)
            _ai_load_error = None
            return True
        except Exception as fallback_exc:
            _ai_load_error = str(fallback_exc)
            return False


def is_image_model_loaded() -> bool:
    return _caption_pipeline is not None


def is_ai_image_model_loaded() -> bool:
    return _ai_image_pipeline is not None


def get_image_load_error() -> str | None:
    return _load_error or _ai_load_error


def _caption_image(image_bytes: bytes) -> str:
    if not load_image_model() or _caption_pipeline is None:
        return ""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    outputs = _caption_pipeline(image)
    if not outputs:
        return ""
    first = outputs[0]
    if isinstance(first, dict):
        return str(first.get("generated_text", "")).strip()
    return str(first).strip()


def _classify_ai_image(image_bytes: bytes) -> tuple[bool, float, str]:
    if not load_ai_image_classifier() or _ai_image_pipeline is None:
        return False, 0.0, ""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    outputs = _ai_image_pipeline(image)
    if not outputs:
        return False, 0.0, ""
    top = outputs[0] if isinstance(outputs, list) else outputs
    label = str(top.get("label", ""))
    score = float(top.get("score", 0.0))
    fake = _label_is_fake(label) or "artificial" in label.lower() or "ai" in label.lower()
    return fake, round(score * 100, 1), label


def detect_image(image_bytes: bytes, filename: str | None = None) -> dict:
    ai_fake, ai_conf, ai_label = _classify_ai_image(image_bytes)
    caption = _caption_image(image_bytes)

    if caption:
        result = detect_text(caption)
        result["model"] = f"{config.MODEL_IMAGE_CAPTION} -> {result['model']}"
        result["reason"] = f'Caption: "{caption[:180]}". {result["reason"]}'
    else:
        result = {
            "fake": ai_fake,
            "confidence": ai_conf or 50.0,
            "reason": "Caption model unavailable.",
            "model": "fallback",
            "labels": [],
        }

    if ai_label:
        result["labels"] = [
            {"label": f"ai-image:{ai_label}", "score": ai_conf / 100},
            *result.get("labels", []),
        ]
        if ai_fake and ai_conf >= 60:
            result["fake"] = True
            result["confidence"] = max(result["confidence"], ai_conf)
            result["reason"] = (
                f"AI-image detector ({ai_label}, {ai_conf:.0f}%). {result['reason']}"
            )
            result["model"] = f"{config.MODEL_IMAGE_AI} + {result['model']}"

    if filename:
        result["labels"] = [{"label": "image", "score": 1.0}, *result.get("labels", [])]

    return result
