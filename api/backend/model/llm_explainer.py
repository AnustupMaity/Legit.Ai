import json
import re

import config


def _parse_json_from_text(text: str) -> dict | None:
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def explain_with_gemini(
    content: str,
    *,
    content_type: str,
    classifier_label: str,
    classifier_score: float,
    fake: bool,
) -> dict | None:
    if not config.USE_LLM or not config.GEMINI_API_KEY:
        return None

    try:
        import google.generativeai as genai

        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        prompt = f"""You are a misinformation analyst. Analyze this {content_type} content.

Content:
\"\"\"{content[:3000]}\"\"\"

Classifier output: label={classifier_label}, score={classifier_score:.4f}, predicted_fake={fake}

Respond with ONLY valid JSON (no markdown):
{{
  "fake": true or false,
  "confidence": 0-100 number,
  "reason": "one or two sentences",
  "categories": ["fake-news", "misinformation", "spam", "safe", etc]
}}"""
        response = model.generate_content(prompt)
        parsed = _parse_json_from_text(response.text or "")
        if parsed and "reason" in parsed:
            return parsed
    except Exception:
        return None
    return None
