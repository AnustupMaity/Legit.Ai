# Minimal fake news text detection using free tools.
# Simple keyword-based approach for demonstration.

FAKE_NEWS_KEYWORDS = [
	"shocking", "miracle", "cure", "click here", "unbelievable", "you won't believe", "secret", "conspiracy"
]

def is_fake_news(text: str) -> bool:
	text_lower = text.lower()
	for keyword in FAKE_NEWS_KEYWORDS:
		if keyword in text_lower:
			return True
	return False

def detect_fake_news(text: str) -> dict:
	"""
	Returns a dict with detection result and reason.
	"""
	if is_fake_news(text):
		return {"fake": True, "reason": "Suspicious keywords detected."}
	return {"fake": False, "reason": "No suspicious keywords found."}
