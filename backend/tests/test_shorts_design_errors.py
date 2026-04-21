import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


class ShortsDesignErrorTests(unittest.TestCase):
    def test_design_shorts_raises_when_provider_call_fails(self):
        from services import claude_service

        transcript = [
            {
                "text": "This is a complete thought that can become a short.",
                "start_ms": 0,
                "end_ms": 30000,
            }
        ]

        with patch.object(claude_service, "_chat", side_effect=RuntimeError("missing API key")):
            with self.assertRaisesRegex(RuntimeError, "Shorts design failed"):
                claude_service.design_shorts(transcript, max_shorts=1)

    def test_design_shorts_raises_when_provider_returns_no_valid_designs(self):
        from services import claude_service

        transcript = [
            {
                "text": "This is a complete thought that can become a short.",
                "start_ms": 0,
                "end_ms": 30000,
            }
        ]

        with patch.object(claude_service, "_chat", return_value='[{"title": "Bad", "segments": []}]'):
            with self.assertRaisesRegex(RuntimeError, "no valid shorts"):
                claude_service.design_shorts(transcript, max_shorts=1)

    def test_design_shorts_returns_empty_for_transcripts_too_short_for_shorts(self):
        from services import claude_service

        transcript = [
            {
                "text": "A short intro.",
                "start_ms": 0,
                "end_ms": 12000,
            }
        ]

        with patch.object(claude_service, "_chat") as chat:
            self.assertEqual(claude_service.design_shorts(transcript, max_shorts=1), [])
            chat.assert_not_called()


if __name__ == "__main__":
    unittest.main()
