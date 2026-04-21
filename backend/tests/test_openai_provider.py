import importlib
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

MODULES_TO_RELOAD = ["config", "services.claude_service"]


def load_claude_service_with_openai():
    os.environ["AI_PROVIDER"] = "openai"
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["OPENAI_MODEL"] = "gpt-test"

    for module_name in MODULES_TO_RELOAD:
        sys.modules.pop(module_name, None)

    return importlib.import_module("services.claude_service")


class OpenAIProviderTests(unittest.TestCase):
    def tearDown(self):
        for key in ["AI_PROVIDER", "OPENAI_API_KEY", "OPENAI_MODEL"]:
            os.environ.pop(key, None)
        for module_name in MODULES_TO_RELOAD:
            sys.modules.pop(module_name, None)

    def test_settings_read_openai_provider_variables(self):
        claude_service = load_claude_service_with_openai()

        self.assertEqual(claude_service.settings.ai_provider, "openai")
        self.assertEqual(claude_service.settings.openai_api_key, "test-openai-key")
        self.assertEqual(claude_service.settings.openai_model, "gpt-test")

    def test_chat_routes_openai_provider_to_responses_api(self):
        claude_service = load_claude_service_with_openai()
        claude_service.client = SimpleNamespace(
            messages=SimpleNamespace(
                create=Mock(side_effect=AssertionError("Anthropic should not be called"))
            )
        )

        response = Mock()
        response.raise_for_status = Mock()
        response.json.return_value = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "OpenAI result",
                        }
                    ],
                }
            ]
        }

        with patch("httpx.post", return_value=response) as post:
            result = claude_service._chat("hello", max_tokens=321, system="developer note")

        self.assertEqual(result, "OpenAI result")
        post.assert_called_once()
        _, kwargs = post.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-openai-key")
        self.assertEqual(kwargs["json"]["model"], "gpt-test")
        self.assertEqual(kwargs["json"]["input"], "hello")
        self.assertEqual(kwargs["json"]["instructions"], "developer note")
        self.assertEqual(kwargs["json"]["max_output_tokens"], 321)


if __name__ == "__main__":
    unittest.main()
