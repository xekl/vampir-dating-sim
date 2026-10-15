import json
import os
from pathlib import Path
from typing import List, Dict, Any

CHARACTERS_DIR = Path(__file__).parent / "characters"


def resolve_profile_image_path(profile_image: str | None) -> str | None:
    """Resolve a character profile image to a real file on disk."""
    if not profile_image:
        return None

    if profile_image.startswith(("http://", "https://", "data:")):
        return profile_image

    image_name = Path(profile_image).name
    candidates = [
        CHARACTERS_DIR / image_name,
        CHARACTERS_DIR / profile_image,
        Path(__file__).parent / image_name,
        Path(__file__).parent / profile_image,
        Path(__file__).parent / "images" / image_name,
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return str(candidate)

    return None


def load_all_characters() -> List[Dict[str, Any]]:
    """Load all character profiles from JSON files"""
    characters = []
    
    if not CHARACTERS_DIR.exists():
        return characters
    
    for json_file in sorted(CHARACTERS_DIR.glob("*.json")):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                character = json.load(f)
                character["profile_image_path"] = resolve_profile_image_path(
                    character.get("profile_image")
                )
                characters.append(character)
        except Exception as e:
            print(f"Error loading character {json_file}: {e}")
    
    return characters
