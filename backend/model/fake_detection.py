# Unified fake detection interface (text, image, etc.)
from .ai_text_detection import detect_fake_news

def detect(content: str, type_: str = "text") -> dict:
	if type_ == "text":
		return detect_fake_news(content)
	elif type_ == "image":
		# Placeholder for image detection
		return {"fake": False, "reason": "Image detection not implemented."}
	else:
		return {"error": "Unsupported type."}
