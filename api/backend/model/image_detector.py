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
        from transformers import BlipProcessor, BlipForConditionalGeneration

        kwargs = {"pretrained_model_name_or_path": config.MODEL_IMAGE_CAPTION}
        processor = BlipProcessor.from_pretrained(**kwargs)
        model = BlipForConditionalGeneration.from_pretrained(**kwargs)
        _caption_pipeline = {"processor": processor, "model": model}
        _load_error = None
        return True
    except Exception as exc:
        _load_error = str(exc)
        print(f"\n[CRITICAL ERROR] Failed to load BLIP caption model: {exc}\n")
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
            print(f"\n[CRITICAL ERROR] Failed to load AI Image model: {fallback_exc}\n")
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
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        processor = _caption_pipeline["processor"]
        model = _caption_pipeline["model"]
        
        inputs = processor(image, return_tensors="pt")
        out = model.generate(**inputs, max_new_tokens=50)
        caption = processor.decode(out[0], skip_special_tokens=True)
        return caption.strip()
    except Exception as exc:
        print(f"Captioning error: {exc}")
        return ""


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


def _analyze_exif(image_bytes: bytes) -> tuple[bool, str, float]:
    """Returns (is_suspicious, reason, confidence_boost)."""
    try:
        from PIL import Image, ExifTags
        import io
        image = Image.open(io.BytesIO(image_bytes))
        exif = image.getexif()
        if not exif:
            return False, "No EXIF data found (common in web images).", 0.0
            
        exif_dict = {}
        for k, v in exif.items():
            tag = ExifTags.TAGS.get(k, k)
            exif_dict[str(tag)] = str(v)
            
        software = exif_dict.get("Software", "").lower()
        if any(ai_tool in software for ai_tool in ["midjourney", "dall-e", "stable diffusion", "ai", "generative"]):
            return True, f"EXIF Software tag indicates AI generation ({software}).", 40.0
        if "photoshop" in software or "adobe" in software:
            return True, f"EXIF Software tag indicates digital editing ({software}).", 20.0
            
        return False, "EXIF data appears normal or heavily stripped.", 0.0
    except Exception as e:
        return False, f"EXIF analysis failed: {e}", 0.0


def _analyze_ela(image_bytes: bytes) -> tuple[bool, str, float]:
    """Error Level Analysis. Returns (is_suspicious, reason, confidence_boost)."""
    try:
        import io
        import numpy as np
        from PIL import Image, ImageChops, ImageEnhance
        
        # Save at 90% quality
        original = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        temp_io = io.BytesIO()
        original.save(temp_io, "JPEG", quality=90)
        temp_io.seek(0)
        resaved = Image.open(temp_io).convert("RGB")
        
        # Calculate difference
        ela_image = ImageChops.difference(original, resaved)
        extrema = ela_image.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        if max_diff == 0:
            max_diff = 1
        scale = 255.0 / max_diff
        ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
        
        # Calculate variance
        ela_array = np.array(ela_image)
        variance = float(np.var(ela_array))
        
        if variance > 1000:  # Arbitrary threshold for high compression variance
            return True, f"High ELA variance ({variance:.1f}) detected. Possible image splicing or heavy editing.", 15.0
        return False, f"ELA variance ({variance:.1f}) within normal bounds.", 0.0
    except Exception as e:
        return False, f"ELA analysis failed: {e}", 0.0


def _analyze_image_with_gemini(image_bytes: bytes) -> dict | None:
    if not config.USE_LLM or not config.GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai
        import re
        import json
        
        genai.configure(api_key=config.GEMINI_API_KEY)
        # Gemini 1.5 models support multimodal input
        model_name = config.GEMINI_MODEL
        if not model_name or "gemini" not in model_name:
            model_name = "gemini-2.5-flash"
        model = genai.GenerativeModel(model_name)
        
        image = Image.open(io.BytesIO(image_bytes))
        prompt = """You are a strict misinformation and deepfake analyst. Analyze this image. Is it an AI-generated deepfake/manipulated or authentic? Look for common deepfake artifacts like unnatural textures, mismatched lighting, text distortions, or anatomical anomalies.

Respond with ONLY valid JSON (no markdown):
{
  "fake": true or false,
  "confidence": 0-100 number,
  "reason": "one or two sentences explaining why it is fake or authentic."
}"""
        response = model.generate_content([prompt, image])
        match = re.search(r"\{[^{}]*\}", response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"Gemini image API error: {e}")
    return None


def detect_image(image_bytes: bytes, filename: str | None = None) -> dict:
    exif_suspicious, exif_reason, exif_boost = _analyze_exif(image_bytes)
    ela_suspicious, ela_reason, ela_boost = _analyze_ela(image_bytes)
    
    ai_fake, ai_conf, ai_label = _classify_ai_image(image_bytes)
    caption = _caption_image(image_bytes)

    local_model_failed = False

    # 1. BASE LOCAL RESULT
    if caption:
        result = detect_text(caption)
        result["model"] = f"{config.MODEL_IMAGE_CAPTION} -> {result['model']}"
        result["reason"] = f'Caption: "{caption[:180]}". {result["reason"]}'
    elif is_image_model_loaded():
        result = {
            "fake": ai_fake,
            "confidence": ai_conf or 50.0,
            "reason": "Image analyzed locally (no caption generated).",
            "model": config.MODEL_IMAGE_CAPTION,
            "labels": [],
        }
    else:
        local_model_failed = True
        err_msg = get_image_load_error() or "Unknown error"
        result = {
            "fake": ai_fake,
            "confidence": ai_conf or 50.0,
            "reason": f"Caption model unavailable. Error: {err_msg}",
            "model": "fallback",
            "labels": [],
        }

    # 2. LOCAL AI IMAGE CLASSIFIER
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
            if local_model_failed:
                result["model"] = config.MODEL_IMAGE_AI
            else:
                result["model"] = f"{config.MODEL_IMAGE_AI} + {result['model']}"

    # 3. EXIF and ELA
    if exif_suspicious:
        result["fake"] = True
        result["confidence"] = min(99.0, result["confidence"] + exif_boost)
        result["reason"] += f" {exif_reason}"
        result["labels"].append({"label": "exif-anomaly", "score": exif_boost / 100.0})
        
    if ela_suspicious:
        result["fake"] = True
        result["confidence"] = min(99.0, result["confidence"] + ela_boost)
        result["reason"] += f" {ela_reason}"
        result["labels"].append({"label": "ela-anomaly", "score": ela_boost / 100.0})

    # 4. GEMINI INTEGRATION (Fallback OR Copilot)
    gemini_result = _analyze_image_with_gemini(image_bytes)
    if gemini_result:
        gemini_fake = gemini_result.get("fake", False)
        gemini_conf = gemini_result.get("confidence", 50.0)
        gemini_reason = gemini_result.get("reason", "")
        
        if local_model_failed:
            # FALLBACK MODE: Overwrite the ugly error text
            extra_reason = ""
            if exif_suspicious:
                extra_reason += f" {exif_reason}"
            if ela_suspicious:
                extra_reason += f" {ela_reason}"
                
            result["fake"] = gemini_fake or exif_suspicious or ela_suspicious
            result["confidence"] = max(result["confidence"], gemini_conf)
            result["reason"] = f"Gemini Analysis: {gemini_reason}{extra_reason}"
            result["model"] = "gemini-fallback"
        else:
            # COPILOT MODE: Add to existing findings
            if gemini_fake:
                result["fake"] = True
                result["confidence"] = max(result["confidence"], gemini_conf)
                
            result["reason"] += f" | Gemini Analysis: {gemini_reason}"
            if "Gemini" not in result["model"] and "gemini" not in result["model"]:
                result["model"] += " + Gemini"
            
        result["labels"].append({"label": "gemini-analysis", "score": gemini_conf / 100.0})

    if filename:
        result["labels"] = [{"label": "image", "score": 1.0}, *result.get("labels", [])]

    return result
