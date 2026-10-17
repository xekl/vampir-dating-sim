"""Persistence for game progress via file and gist."""

import json
from typing import Dict

from data_logger import log_to_gist


def store_character_state(username: str, character_state: Dict) -> None:

    # build filename from user/character combination
    target_file = "fangtastic_" + username + "_" + character_state.get("id")

    # select character content to store 
    character_content = {
        "messages": character_state.get("messages"),
        "interest_level": character_state.get("interest_level"),
        "meeting_planned": character_state.get("meeting_planned"),
        "blocked_user": character_state.get("blocked_user")
    }
    json_to_store = json.dumps(character_content, ensure_ascii=False, indent=2)

    # store in gist 
    #TODO make storing in files possible?
    response = log_to_gist(target_file, json_to_store, mode="replace")
    # print("store_character_state response:", response.status_code, response.text)
    print("store_character_state response:", response.status_code)
    

def store_user_profile(username: str, profile_data: Dict) -> None:
    
    # build filename from username
    target_file = "fangtastic_" + username + "_profile"

    json_to_store = json.dumps(profile_data, ensure_ascii=False, indent=2)

    # store in gist 
    #TODO make storing in files possible?
    response = log_to_gist(target_file, json_to_store, mode="replace")
    # print("store_user_profile response:", response.status_code, response.text)
    print("store_user_profile response:", response.status_code)

