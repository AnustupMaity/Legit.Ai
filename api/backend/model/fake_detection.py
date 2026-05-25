from backend.model.image_detector import (
    detect_image,
    load_ai_image_classifier,
    load_image_model,
)
from backend.model.text_detector import detect_text, load_text_model


def preload_models() -> dict[str, bool]:
    return {
        "text": load_text_model(),
        "image_caption": load_image_model(),
        "image_ai": load_ai_image_classifier(),
    }


def detect(content: str, type_: str = "text", image_bytes: bytes | None = None, filename: str | None = None) -> dict:
    if type_ == "text":
        return detect_text(content)
    if type_ == "image" and image_bytes is not None:
        return detect_image(image_bytes, filename=filename)
    return {"error": "Unsupported type or missing image data."}
