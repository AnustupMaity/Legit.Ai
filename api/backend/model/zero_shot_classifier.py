from __future__ import annotations

import config

_zero_shot_pipeline = None
_load_error: str | None = None


def load_zero_shot_model() -> bool:
    global _zero_shot_pipeline, _load_error
    if _zero_shot_pipeline is not None:
        return True
    try:
        from transformers import pipeline

        kwargs = {"model": config.MODEL_ZERO_SHOT}
        if config.HF_TOKEN:
            kwargs["token"] = config.HF_TOKEN
        _zero_shot_pipeline = pipeline(
            "zero-shot-classification",
            device=config.DEVICE,
            **kwargs,
        )
        _load_error = None
        return True
    except Exception as exc:
        _load_error = str(exc)
        _zero_shot_pipeline = None
        return False


def is_zero_shot_model_loaded() -> bool:
    return _zero_shot_pipeline is not None


def get_zero_shot_load_error() -> str | None:
    return _load_error


def classify_zero_shot(text: str, categories: list[str] | None = None) -> dict:
    """
    Classify text into arbitrary categories using zero-shot classification.
    
    Args:
        text: The text to classify
        categories: List of category labels (defaults to config.ZERO_SHOT_CATEGORIES)
    
    Returns:
        dict with keys: labels, scores, sequence, top_category, top_score
    """
    if not load_zero_shot_model() or _zero_shot_pipeline is None:
        return {
            "error": "Zero-shot model unavailable",
            "labels": [],
            "scores": [],
        }

    if categories is None:
        categories = config.ZERO_SHOT_CATEGORIES

    try:
        result = _zero_shot_pipeline(text, categories, multi_label=True)
        
        # Format results
        labels = result.get("labels", [])
        scores = result.get("scores", [])
        
        # Create labeled pairs
        labeled_scores = [
            {"label": label, "score": round(score, 3)}
            for label, score in zip(labels, scores)
        ]
        
        # Get top category
        top_category = labels[0] if labels else "unknown"
        top_score = round(scores[0] * 100, 1) if scores else 0.0
        
        return {
            "labels": labeled_scores,
            "sequence": result.get("sequence", text[:100]),
            "top_category": top_category,
            "top_score": top_score,
        }
    except Exception as exc:
        return {
            "error": f"Zero-shot classification failed: {str(exc)}",
            "labels": [],
            "scores": [],
        }


def get_category_signals(text: str) -> dict:
    """
    Get category classification signals for text analysis.
    
    Returns categories that might indicate fake/suspicious content.
    """
    result = classify_zero_shot(text)
    
    suspicious_categories = ["propaganda", "conspiracy", "clickbait", "satire"]
    
    if "error" in result:
        return {"suspicious": False, "categories": [], "error": result["error"]}
    
    labels = result.get("labels", [])
    
    # Check for suspicious categories
    suspicious_matches = [
        label for label in labels 
        if label["label"].lower() in suspicious_categories and label["score"] > 0.3
    ]
    
    return {
        "suspicious": len(suspicious_matches) > 0,
        "categories": labels,
        "suspicious_matches": suspicious_matches,
        "top_category": result.get("top_category"),
    }
