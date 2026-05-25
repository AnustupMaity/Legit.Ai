from backend.model.audio_detector import (
    detect_audio,
    get_audio_load_error,
    is_audio_model_loaded,
    load_audio_model,
)
from backend.model.document_processor import (
    analyze_document_batch,
    detect_document,
    extract_text_from_document,
)
from backend.model.fact_checker import (
    check_facts,
    get_embedding_load_error,
    get_knowledge_base,
    initialize_knowledge_base,
    integrate_fact_check,
    is_embedding_model_loaded,
)
from backend.model.image_detector import (
    detect_image,
    get_image_load_error,
    is_ai_image_model_loaded,
    is_image_model_loaded,
    load_ai_image_classifier,
    load_image_model,
)
from backend.model.llm_explainer import explain_with_gemini
from backend.model.text_detector import (
    detect_text,
    get_text_load_error,
    is_enhanced_model_loaded,
    is_text_model_loaded,
    load_enhanced_model,
    load_text_model,
)
from backend.model.url_fetcher import fetch_article_text
from backend.model.video_detector import detect_video
from backend.model.zero_shot_classifier import (
    classify_zero_shot,
    get_category_signals,
    get_zero_shot_load_error,
    is_zero_shot_model_loaded,
    load_zero_shot_model,
)

__all__ = [
    "detect_audio",
    "detect_document",
    "detect_image",
    "detect_text",
    "detect_video",
    "explain_with_gemini",
    "extract_text_from_document",
    "fetch_article_text",
    "analyze_document_batch",
    "get_audio_load_error",
    "get_embedding_load_error",
    "get_image_load_error",
    "get_knowledge_base",
    "get_text_load_error",
    "get_zero_shot_load_error",
    "is_audio_model_loaded",
    "is_ai_image_model_loaded",
    "is_embedding_model_loaded",
    "is_enhanced_model_loaded",
    "is_image_model_loaded",
    "is_text_model_loaded",
    "is_zero_shot_model_loaded",
    "initialize_knowledge_base",
    "integrate_fact_check",
    "load_audio_model",
    "load_ai_image_classifier",
    "load_enhanced_model",
    "load_image_model",
    "load_text_model",
    "load_zero_shot_model",
    "classify_zero_shot",
    "get_category_signals",
    "check_facts",
]
