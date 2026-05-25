import logging
from typing import Any, Dict, List

try:
    import shap
    import torch
    from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

logger = logging.getLogger(__name__)

class TextExplainer:
    def __init__(self, model_path: str = "distilbert-base-uncased", tokenizer_path: str | None = None):
        self.model_path = model_path
        self.tokenizer_path = tokenizer_path or model_path
        self.pipeline = None
        self.explainer = None
        self._load_model()

    def _load_model(self):
        if not SHAP_AVAILABLE:
            logger.warning("SHAP or Transformers not available. Explainer will be disabled.")
            return

        try:
            model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
            tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_path)
            self.pipeline = pipeline("text-classification", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)
            self.explainer = shap.Explainer(self.pipeline)
        except Exception as e:
            logger.error(f"Failed to load model for XAI: {e}")

    def explain(self, texts: List[str]) -> List[Dict[str, Any]]:
        if not SHAP_AVAILABLE or not self.explainer:
            return [{"error": "Explainer not initialized or SHAP not installed."} for _ in texts]

        try:
            shap_values = self.explainer(texts)
            results = []
            for i in range(len(texts)):
                # Return token-level contributions
                results.append({
                    "text": texts[i],
                    "tokens": shap_values.data[i].tolist() if hasattr(shap_values.data[i], "tolist") else shap_values.data[i],
                    "values": shap_values.values[i].tolist() if hasattr(shap_values.values[i], "tolist") else shap_values.values[i],
                    "base_values": float(shap_values.base_values[i]) if hasattr(shap_values.base_values, "__getitem__") else float(shap_values.base_values)
                })
            return results
        except Exception as e:
            logger.error(f"SHAP Explanation failed: {e}")
            return [{"error": str(e)} for _ in texts]

# Singleton instance for generic explaining (can be overridden by specific models)
default_explainer = TextExplainer()
