import json
from pathlib import Path
from typing import Any, Dict, List

USERS_DIR = Path(__file__).parent / "users"


def load_all_users() -> List[Dict[str, Any]]:
    """Load user login, profile, and character-association data from JSON files."""
    users = []
    if not USERS_DIR.exists():
        return users

    for json_file in sorted(USERS_DIR.glob("*.json")):
        try:
            with json_file.open("r", encoding="utf-8") as handle:
                user = json.load(handle)
            if user.get("username"):
                users.append(user)
        except (OSError, json.JSONDecodeError) as error:
            print(f"Error loading user {json_file}: {error}")

    return users


def users_by_username(users: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Index loaded users for login and session-state lookups."""
    return {user["username"]: user for user in users if user.get("username")}
