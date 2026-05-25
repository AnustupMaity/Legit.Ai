import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

# Use isolated DB for tests
_test_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db.name}"
os.environ["USE_LLM"] = "false"
os.environ["EAGER_LOAD_MODELS"] = "false"

from db.database import init_db  # noqa: E402
from main import app  # noqa: E402


class TestMainAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_read_root_status_code(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_read_root_content(self):
        response = self.client.get("/")
        self.assertEqual(response.json(), {"message": "Legit.ai API is running"})

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("text_model_loaded", data)

    @patch("backend.model.fake_detection.detect")
    def test_detect_text(self, mock_detect):
        mock_detect.return_value = {
            "fake": True,
            "confidence": 88.5,
            "reason": "Test reason",
            "model": "test-model",
            "labels": [{"label": "FAKE", "score": 0.88}],
        }
        response = self.client.post(
            "/detect/text",
            json={"text": "shocking miracle cure click here"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["fake"])
        self.assertEqual(data["confidence"], 88.5)
        self.assertIsNotNone(data["id"])

    def test_detect_text_validation(self):
        response = self.client.post("/detect/text", json={"text": ""})
        self.assertEqual(response.status_code, 422)

    def test_history_empty_ok(self):
        response = self.client.get("/history")
        self.assertEqual(response.status_code, 200)
        self.assertIn("items", response.json())

    def test_stats(self):
        response = self.client.get("/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("scanned_today", data)


if __name__ == "__main__":
    unittest.main()
