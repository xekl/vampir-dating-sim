import json
from pathlib import Path
from typing import Any, Dict, List

USERS_DIR = Path(__file__).parent / "users"
CHARACTERS_DIR = Path(__file__).parent / "characters"


def load_all_users() -> List[Dict[str, Any]]:
    """Load user login, profile, and character-association data from JSON files."""
    users = []

    if not USERS_DIR.exists():
        #TODO add error logging in error gist 
        return users

    for json_file in sorted(USERS_DIR.glob("*.json")):
        try:
            with json_file.open("r", encoding="utf-8") as handle:
                user = json.load(handle)
            if user.get("username"):
                users.append(user)
        except (OSError, json.JSONDecodeError) as error:
            #TODO add error logging in error gist 
            print(f"Error loading user {json_file}: {error}")

    return users


def get_user_by_username(users: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Index loaded users for login and session-state lookups."""
    return {user["username"]: user for user in users if user.get("username")}


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
        #TODO add error logging in error gist 
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
            #TODO add error logging in error gist 
            print(f"Error loading character {json_file}: {e}")
    
    return characters
