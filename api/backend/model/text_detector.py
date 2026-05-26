from __future__ import annotations

import config
from backend.model.llm_explainer import explain_with_gemini
from backend.model.zero_shot_classifier import get_category_signals

FAKE_NEWS_KEYWORDS = [
    "shocking",
    "miracle",
    "cure",
    "click here",
    "unbelievable",
    "you won't believe",
    "secret",
    "conspiracy",
]

_text_pipeline = None
_enhanced_pipeline = None
_zero_shot_enabled = True
_load_error: str | None = None
_enhanced_load_error: str | None = None


def _keyword_fallback(text: str) -> tuple[bool, float, str, str]:
    text_lower = text.lower()
    for keyword in FAKE_NEWS_KEYWORDS:
        if keyword in text_lower:
            return True, 65.0, "Suspicious keywords detected.", "keyword-fallback"
    return False, 55.0, "No suspicious keywords found.", "keyword-fallback"


def _label_is_fake(label: str) -> bool:
    normalized = label.upper().replace("_", " ").replace("-", " ")
    fake_tokens = ("FAKE", "FALSE", "MISINFO", "UNRELIABLE", "LABEL_1")
    real_tokens = ("REAL", "TRUE", "RELIABLE", "LABEL_0")
    if any(t in normalized for t in fake_tokens):
        if any(t in normalized for t in real_tokens) and "FAKE" not in normalized:
            return False
        return True
    if any(t in normalized for t in real_tokens):
        return False
    return "FAKE" in normalized or label == "1"


def load_text_model() -> bool:
    global _text_pipeline, _load_error
    if _text_pipeline is not None:
        return True
    try:
        from transformers import pipeline

        kwargs = {"model": config.MODEL_TEXT}
        if config.HF_TOKEN:
            kwargs["token"] = config.HF_TOKEN
        _text_pipeline = pipeline(
            "text-classification",
            device=config.DEVICE,
            **kwargs,
            truncation=True,
            max_length=512,
        )
        _load_error = None
        return True
    except Exception as exc:
        print(f"CRITICAL: Failed to load text model: {exc}")
        _load_error = str(exc)
        _text_pipeline = None
        return False


def load_enhanced_model() -> bool:
    global _enhanced_pipeline, _enhanced_load_error
    if _enhanced_pipeline is not None:
        return True
    try:
        from transformers import pipeline

        kwargs = {"model": config.MODEL_TEXT_ENHANCED}
        if config.HF_TOKEN:
            kwargs["token"] = config.HF_TOKEN
        _enhanced_pipeline = pipeline(
            "text-classification",
            device=config.DEVICE,
            **kwargs,
            truncation=True,
            max_length=512,
        )
        _enhanced_load_error = None
        return True
    except Exception as exc:
        print(f"CRITICAL: Failed to load enhanced text model: {exc}")
        _enhanced_load_error = str(exc)
        _enhanced_pipeline = None
        return False


def is_text_model_loaded() -> bool:
    return _text_pipeline is not None


def is_enhanced_model_loaded() -> bool:
    return _enhanced_pipeline is not None


def get_text_load_error() -> str | None:
    return _load_error or _enhanced_load_error


def _ensemble(
    clf_fake: bool,
    clf_conf: float,
    kw_fake: bool,
    kw_conf: float,
    enhanced_fake: bool | None = None,
    enhanced_conf: float | None = None,
    zero_shot_suspicious: bool = False,
) -> tuple[bool, float, str, list[str]]:
    """
    Enhanced ensemble voting with multiple signals.
    
    Returns:
        (is_fake, confidence, reason, signal_sources)
    """
    signals = []
    fake_votes = 0
    real_votes = 0
    confidences = []
    
    # Base classifier
    if clf_fake:
        fake_votes += 1
        signals.append("base-classifier")
        confidences.append(clf_conf)
    else:
        real_votes += 1
        confidences.append(100 - clf_conf)
    
    # Enhanced classifier
    if enhanced_fake is not None:
        if enhanced_fake:
            fake_votes += 1
            signals.append("enhanced-classifier")
            confidences.append(enhanced_conf)
        else:
            real_votes += 1
            confidences.append(100 - enhanced_conf)
    
    # Keyword fallback
    if kw_fake:
        fake_votes += 1
        signals.append("keywords")
        confidences.append(kw_conf)
    else:
        real_votes += 1
        confidences.append(100 - kw_conf)
    
    # Zero-shot classification
    if zero_shot_suspicious:
        fake_votes += 1
        signals.append("zero-shot-categories")
        confidences.append(70.0)  # Moderate confidence for category signal
    
    # Calculate weighted confidence
    if confidences:
        avg_conf = sum(confidences) / len(confidences)
    else:
        avg_conf = 50.0
    
    # Voting decision
    total_votes = fake_votes + real_votes
    if total_votes == 0:
        return False, 50.0, "No classification signals available.", []
    
    # Majority vote with confidence boost for agreement
    if fake_votes > real_votes:
        # Strong agreement among fake signals
        if fake_votes >= total_votes * 0.7:
            final_conf = min(99.0, avg_conf + 10)
            reason = f"Strong agreement among {fake_votes} fake signals: {', '.join(signals)}."
        else:
            final_conf = min(95.0, avg_conf + 5)
            reason = f"Majority vote ({fake_votes}/{total_votes}) indicates fake: {', '.join(signals)}."
        return True, round(final_conf, 1), reason, signals
    elif real_votes > fake_votes:
        if real_votes >= total_votes * 0.7:
            final_conf = max(1.0, avg_conf - 10)
            reason = f"Strong agreement among {real_votes} authentic signals: {', '.join(signals)}."
        else:
            final_conf = max(5.0, avg_conf - 5)
            reason = f"Majority vote ({real_votes}/{total_votes}) indicates authentic: {', '.join(signals)}."
        return False, round(final_conf, 1), reason, signals
    else:
        # Tie - use keyword as tiebreaker or default to cautious
        if kw_fake:
            return True, round(avg_conf + 3, 1), f"Tie broken by keyword signal: {', '.join(signals)}.", signals
        return False, round(max(30.0, avg_conf - 5), 1), f"Tie - defaulting to authentic: {', '.join(signals)}.", signals


def _classify(text: str) -> tuple[bool, float, str, str, list[dict]]:
    kw_fake, kw_conf, kw_reason, kw_model = _keyword_fallback(text)
    
    # Load enhanced model if available
    enhanced_fake = None
    enhanced_conf = None
    if load_enhanced_model() and _enhanced_pipeline:
        try:
            enhanced_results = _enhanced_pipeline(text[:5000])
            if enhanced_results:
                enhanced_top = enhanced_results[0] if isinstance(enhanced_results, list) else enhanced_results
                enhanced_label = str(enhanced_top.get("label", "UNKNOWN"))
                enhanced_score = float(enhanced_top.get("score", 0.5))
                enhanced_fake = _label_is_fake(enhanced_label)
                enhanced_conf = round(enhanced_score * 100, 1)
                if not enhanced_fake:
                    enhanced_conf = round((1 - enhanced_score) * 100, 1) if enhanced_score < 0.5 else enhanced_conf
        except Exception as exc:
            print(f"Enhanced model inference failed: {exc}")

    # Get zero-shot category signals
    zero_shot_suspicious = False
    if _zero_shot_enabled:
        try:
            category_signals = get_category_signals(text)
            zero_shot_suspicious = category_signals.get("suspicious", False)
        except Exception as exc:
            print(f"Zero-shot classification failed: {exc}")

    if not load_text_model() or _text_pipeline is None:
        # Use only enhanced model if base failed
        if enhanced_fake is not None:
            fake, confidence, reason, signals = _ensemble(
                enhanced_fake, enhanced_conf, kw_fake, kw_conf,
                None, None, zero_shot_suspicious
            )
            model_used = config.MODEL_TEXT_ENHANCED
            labels = [{"label": "enhanced-classifier", "score": enhanced_conf / 100}]
        else:
            fake, confidence, reason, signals = _ensemble(
                False, 50.0, kw_fake, kw_conf,
                None, None, zero_shot_suspicious
            )
            model_used = kw_model
            labels = [{"label": "keywords", "score": kw_conf / 100}]
        
        labels.append({"label": "keywords", "score": kw_conf / 100})
        if zero_shot_suspicious:
            labels.append({"label": "zero-shot-suspicious", "score": 0.7})
        
        return fake, confidence, reason, model_used, labels

    results = _text_pipeline(text[:5000])
    if not results:
        if enhanced_fake is not None:
            fake, confidence, reason, signals = _ensemble(
                enhanced_fake, enhanced_conf, kw_fake, kw_conf,
                None, None, zero_shot_suspicious
            )
            model_used = config.MODEL_TEXT_ENHANCED
            labels = [{"label": "enhanced-classifier", "score": enhanced_conf / 100}]
        else:
            fake, confidence, reason, signals = _ensemble(
                False, 50.0, kw_fake, kw_conf,
                None, None, zero_shot_suspicious
            )
            model_used = "fallback"
            labels = []
        
        labels.append({"label": "keywords", "score": kw_conf / 100})
        if zero_shot_suspicious:
            labels.append({"label": "zero-shot-suspicious", "score": 0.7})
        
        return fake, confidence, reason, model_used, labels

    top = results[0] if isinstance(results, list) else results
    label = str(top.get("label", "UNKNOWN"))
    score = float(top.get("score", 0.5))
    clf_fake = _label_is_fake(label)
    clf_conf = round(score * 100, 1)
    if not clf_fake:
        clf_conf = round((1 - score) * 100, 1) if score < 0.5 else clf_conf

    fake, confidence, reason, signals = _ensemble(
        clf_fake, clf_conf, kw_fake, kw_conf,
        enhanced_fake, enhanced_conf, zero_shot_suspicious
    )

    # Build labels list
    labels = [
        {"label": str(r.get("label", "")), "score": float(r.get("score", 0))}
        for r in (results if isinstance(results, list) else [results])
    ]
    labels.append({"label": "keywords", "score": kw_conf / 100})
    
    if enhanced_fake is not None:
        labels.append({"label": "enhanced-classifier", "score": enhanced_conf / 100})
    
    if zero_shot_suspicious:
        labels.append({"label": "zero-shot-suspicious", "score": 0.7})
    
    # Determine which model to report
    model_used = config.MODEL_TEXT
    if enhanced_fake is not None:
        model_used = f"{config.MODEL_TEXT}+{config.MODEL_TEXT_ENHANCED}"
    if zero_shot_suspicious:
        model_used = f"{model_used}+zero-shot"
    
    return fake, confidence, reason, model_used, labels


def detect_text(text: str) -> dict:
    fake, confidence, reason, model, labels = _classify(text)
    classifier_label = labels[0]["label"] if labels else ("FAKE" if fake else "REAL")
    classifier_score = labels[0]["score"] if labels else confidence / 100

    llm = explain_with_gemini(
        text,
        content_type="text",
        classifier_label=classifier_label,
        classifier_score=classifier_score,
        fake=fake,
    )
    if llm:
        fake = bool(llm.get("fake", fake))
        confidence = float(llm.get("confidence", confidence))
        reason = str(llm.get("reason", reason))
        categories = llm.get("categories", [])
        if categories:
            labels = [{"label": c, "score": 1.0} for c in categories]

    return {
        "fake": fake,
        "confidence": min(100.0, max(0.0, confidence)),
        "reason": reason,
        "model": model if not llm else f"{model}+gemini",
        "labels": labels,
    }
