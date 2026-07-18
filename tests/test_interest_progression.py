import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from groq_api import derive_interest_state


class InterestProgressionTests(unittest.TestCase):
    def test_interest_grows_slowly_for_light_chat(self):
        previous = {"meeting_planned": False, "interest_level": 40, "reason": "Leichter Start"}
        state = derive_interest_state(
            "Isabelle",
            "Du bist romantisch und vorsichtig.",
            previous,
            [{"role": "user", "content": "Hallo, wie geht es dir?"}],
        )

        self.assertFalse(state["meeting_planned"])
        self.assertGreaterEqual(state["interest_level"], 40)
        self.assertLess(state["interest_level"] - previous["interest_level"], 15)

    def test_meeting_requires_strong_evidence(self):
        previous = {"meeting_planned": False, "interest_level": 82, "reason": "Starkes Interesse"}
        state = derive_interest_state(
            "Isabelle",
            "Du bist romantisch und vorsichtig.",
            previous,
            [
                {"role": "user", "content": "Ich möchte dich wirklich kennenlernen. Wollen wir uns morgen Abend im Café treffen?"},
                {"role": "assistant", "content": "Ich würde dich gern näher kennenlernen."},
            ],
        )

        self.assertTrue(state["meeting_planned"])
        self.assertGreaterEqual(state["interest_level"], 85)


if __name__ == "__main__":
    unittest.main()
