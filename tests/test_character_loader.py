import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from character_loader import resolve_profile_image_path


class CharacterLoaderTests(unittest.TestCase):
    def test_resolve_profile_image_path_returns_existing_placeholder(self):
        image_path = resolve_profile_image_path("placeholder_1.jpg")

        self.assertIsNotNone(image_path)
        self.assertTrue(Path(image_path).exists())

    def test_resolve_profile_image_path_returns_none_for_missing_file(self):
        self.assertIsNone(resolve_profile_image_path("does_not_exist.jpg"))


if __name__ == "__main__":
    unittest.main()
