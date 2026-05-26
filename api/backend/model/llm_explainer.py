import json
import re

import config
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)


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
        prompt = f"""You are a strict misinformation analyst and fact-checker. Analyze this {content_type} content.

Content:
\"\"\"{content[:3000]}\"\"\"

Classifier output: label={classifier_label}, score={classifier_score:.4f}, predicted_fake={fake}

IMPORTANT INSTRUCTIONS:
1. You MUST independently fact-check any historical or scientific claims in the content.
2. If the content contains blatant factual inaccuracies (e.g. "the sun rises in the south", "the earth is flat"), you MUST override the classifier and set "fake" to true, with a high confidence.
3. If the content is an opinion or subjective statement, rely on the classifier output.

Respond with ONLY valid JSON (no markdown):
{{
  "fake": true or false,
  "confidence": 0-100 number,
  "reason": "one or two sentences explaining why it is fake or authentic, pointing out specific factual inaccuracies if any.",
  "categories": ["fake-news", "misinformation", "spam", "safe"]
}}"""
        response = model.generate_content(prompt)
        parsed = _parse_json_from_text(response.text or "")
        if parsed and "reason" in parsed:
            return parsed
        else:
            print(f"Gemini API returned invalid JSON: {response.text}")
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None
    return None
