"""LLM API wrapper that routes to the selected backend.

This module provides `manage_dialog` and `chat_with_character` functions
with the same signatures and dispatches calls to either the remote Groq client 
or a local Ollama-based implementation, depending on the options in 
`fangtastic_options`.
"""

from typing import Any, Dict, List
from fangtastic_options import OPTIONS
we_use_ollama = str(OPTIONS.get("api_choice", "groq")).lower() == "ollama"


# Import backends lazily to avoid importing heavy deps when not needed
if we_use_ollama:
    from ollama_api import manage_dialog as _ollama_manage_dialog
    from ollama_api import chat_with_character as _ollama_chat
else: 
    from groq_api import manage_dialog as _groq_manage_dialog
    from groq_api import chat_with_character as _groq_chat


def manage_dialog(character_name: str, character_strategy: str, previous_state: Dict[str, Any], chat_history: List[Dict[str, str]], user_profile: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Dispatch manage_dialog to the selected backend."""

    if we_use_ollama:
        return _ollama_manage_dialog(character_name, character_strategy, previous_state, chat_history, user_profile)
    else:
        return _groq_manage_dialog(character_name, character_strategy, previous_state, chat_history, user_profile)


def chat_with_character(character_description: str, current_time: str, username: str, chat_history: List[Dict[str, str]], management_result: Dict[str, Any], user_message: str, user_profile: Dict[str, Any] | None = None) -> str:
    """Dispatch chat_with_character to the selected backend."""

    if we_use_ollama:
        return _ollama_chat(character_description, current_time, username, chat_history, management_result, user_message, user_profile)
    else:
        return _groq_chat(character_description, current_time, username, chat_history, management_result, user_message, user_profile)
