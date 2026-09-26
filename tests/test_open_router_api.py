import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import open_router_api


class FakeResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": self.content}}]}


class OpenRouterApiTests(unittest.TestCase):
    def test_manage_dialog_uses_openrouter_and_limits_interest_change(self):
        response = FakeResponse(
            '{"interest_level": 100, "meeting_planned": true, "reason": "Gutes Gespräch"}'
        )
        with (
            patch.object(open_router_api, "_get_api_key", return_value="test-key"),
            patch.object(open_router_api.requests, "post", return_value=response) as post,
        ):
            state = open_router_api.manage_dialog(
                "Michi",
                "Vorsichtig und höflich.",
                {"interest_level": 50, "meeting_planned": False},
                [
                    {"role": "user", "content": "Hallo!"},
                    {"role": "assistant", "content": "Guten Abend."},
                ],
            )

        self.assertEqual(state["interest_level"], 65)
        self.assertTrue(state["meeting_planned"])
        self.assertEqual(post.call_args.args[0], open_router_api.OPENROUTER_CHAT_COMPLETIONS_URL)
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(post.call_args.kwargs["json"]["model"], "openai/gpt-4o-mini")

    def test_chat_with_character_returns_answer_after_refusal_check(self):
        responses = [FakeResponse("Hallo, schön dich zu sehen."), FakeResponse("No refusal detected")]
        with (
            patch.object(open_router_api, "_get_api_key", return_value="test-key"),
            patch.object(open_router_api.requests, "post", side_effect=responses) as post,
        ):
            answer = open_router_api.chat_with_character(
                "Ein geheimnisvoller Vampir.",
                "Freitagabend",
                "Alex",
                [],
                {"char_instructions": "Bleib zurückhaltend."},
                "Guten Abend.",
            )

        self.assertEqual(answer, "Hallo, schön dich zu sehen.")
        self.assertEqual(post.call_count, 2)


if __name__ == "__main__":
    unittest.main()