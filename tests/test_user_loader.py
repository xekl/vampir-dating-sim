import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from user_loader import load_all_users, users_by_username


class UserLoaderTests(unittest.TestCase):
    def test_loads_fanggirl_login_profile_and_characters(self):
        users = users_by_username(load_all_users())
        fanggirl = users["fanggirl"]

        self.assertEqual(fanggirl["password"], "blut1234")
        self.assertEqual(fanggirl["profile"]["nickname"], "fanggirl")
        self.assertIn("fanggirl_felix", fanggirl["character_ids"])


if __name__ == "__main__":
    unittest.main()
