"""LLM API wrapper that routes to the selected backend.

This module provides `manage_dialog` and `chat_with_character` functions
with the same signatures and dispatches calls to either the remote Groq client 
or a local Ollama-based implementation, depending on the options in 
`fangtastic_options`.
"""

from typing import Any, Dict, List
from app_options import OPTIONS
from data_logger import log_error, log_other_stuff
import llm_prompt_library
import json 
import re 


api_choice = str(OPTIONS.get("api_choice", "groq")).lower()
print("api_choice:", api_choice)


# Import backend lazily to avoid importing heavy deps when not needed
if api_choice == "ollama":
    from llm_api_ollama import create_chat_completion
    from llm_api_ollama import get_analysis_model
    from llm_api_ollama import get_chat_model
elif api_choice == "open_router":
    from llm_api_open_router import create_chat_completion
    from llm_api_open_router import get_analysis_model
    from llm_api_open_router import get_chat_model
else: 
    from llm_api_groq import create_chat_completion
    from llm_api_groq import get_analysis_model
    from llm_api_groq import get_chat_model


def manage_dialog(character_name: str, character_strategy: str, old_interest_level: int, old_meeting_planned: bool, old_user_blocked: bool, chat_history: List[Dict[str, str]], user_profile: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Dispatch manage_dialog to the selected backend."""

    # skip analysis if nothing to analyse
    if not chat_history or len(chat_history) < 2:
        return {
            "meeting_planned": old_meeting_planned,
            "interest_level": old_interest_level,
            "user_blocked": old_user_blocked,
            "reason": "Noch keine Nachricht.",
            "char_instructions": "",
        }

    # build dialog management prompt from library
    prompt = llm_prompt_library.DIALOG_MANAGEMENT_PROMPT.format(
        character_name=character_name,
        conversation_summary=format_chat_history_for_analysis(chat_history),
        character_strategy=character_strategy,
        user_profile=llm_prompt_library.USER_PROFILE_CONTEXT.format(
            nickname=(user_profile or {}).get("nickname", ""),
            age=(user_profile or {}).get("age", ""),
            gender=(user_profile or {}).get("gender", ""),
            interests=", ".join((user_profile or {}).get("interests", [])),
            looking_for=", ".join((user_profile or {}).get("looking_for", [])),
            bio=(user_profile or {}).get("bio", ""),
        ),
        interest_level=old_interest_level,
        meeting_planned=old_meeting_planned,
        user_blocked=old_user_blocked,
    )

    # call imported chat completion
    try: 
        response_text = create_chat_completion(model=get_analysis_model(), messages=[{"role": "user", "content": prompt}], mode="analysis")
    except Exception as error:
        log_error(username=user_profile.get("nickname", "Unknown User") if user_profile else "No User", position="llm_api.manage_dialog()", error_message=f"Error during analysis response: {error}, raw response_text was: {response_text}")
        print(f"ERROR - llm_api.manage_dialog() - Error during analysis response: {error}, raw response_text was: {response_text}\n\n")

    if OPTIONS.get("debug"): # if in debug mode, log this (otherwise, this takes too much time)
        log_other_stuff(username=user_profile.get("nickname", "Unknown User") if user_profile else "No User", position="llm_api.manage_dialog()", log_message=f"Analysis response: {response_text}")
    print("LOG - llm_api.manage_dialog() - Analysis response: {response_text}\n\n")

    # analyse JSON output if well-formatted
    try:
        match = re.search(r"\{.*\}", response_text, re.S)
        if match: # output seems to be a JSON
            parsed = json.loads(match.group(0))
            new_interest_level = min(100, max(0, int(parsed.get("interest_level", old_interest_level))))
            delta = new_interest_level - old_interest_level
            if abs(delta) > 15:
                new_interest_level = old_interest_level + max(-15, min(15, delta))
            return {
                "meeting_planned": bool(parsed.get("meeting_planned", False)),
                "interest_level": new_interest_level,
                "user_blocked": bool(parsed.get("user_blocked", False)),
                "reason": str(parsed.get("reason", ""))[:160],
                "char_instructions": str(parsed.get("char_instructions", "")),
            }
        else: # no JSON, but still an answer
            return {
                "meeting_planned": old_meeting_planned,
                "interest_level": old_interest_level,
                "user_blocked": old_user_blocked,
                "reason": "Kein JSON, nur: " + response_text,
                "char_instructions": "",
            }
    except Exception as error:
        log_error(username=user_profile.get("nickname", "Unknown User") if user_profile else "No User", position="llm_api.manage_dialog()", error_message=f"Error while analysing JSON output: {error}, raw response_text was: {response_text}")
        print(f"ERROR - llm_api.manage_dialog() - Error while analysing JSON output: {error}, raw response_text was: {response_text}\n\n")
        return {
            "meeting_planned": old_meeting_planned,
            "interest_level": old_interest_level,
            "user_blocked": old_user_blocked,
            "reason": f"Fehler: {str(error)[:140]}",
            "char_instructions": "",
        }


def chat_with_character(character_description: str, current_time: str, chat_history: List[Dict[str, str]], interest_level: int, meeting_planned: bool, user_blocked: bool, next_turn_instructions: str, user_profile: Dict[str, Any] | None = None) -> str:
    """Dispatch chat_with_character to the selected backend."""

    char_system_prompt = llm_prompt_library.CHARACTER_REPLY_PROMPT.format(
        current_time=current_time,
        character_description=character_description,
        user_profile=llm_prompt_library.USER_PROFILE_CONTEXT.format(
            nickname=(user_profile or {}).get("nickname", ""),
            age=(user_profile or {}).get("age", ""),
            gender=(user_profile or {}).get("gender", ""),
            interests=", ".join((user_profile or {}).get("interests", [])),
            looking_for=", ".join((user_profile or {}).get("looking_for", [])),
            bio=(user_profile or {}).get("bio", ""),
        ),
    )
    messages = [{"role": "system", "content": char_system_prompt}]
    messages.extend(chat_history)
    messages.append({
        "role": "system",
        "content": "system_prompt-Ergänzung. In deinem nächsten Turn: " + next_turn_instructions,
    })

    # call imported chat completion
    try: 
        response_text = create_chat_completion(model=get_chat_model(), messages=messages, mode="chat")
    except Exception as error:
        log_error(username=user_profile.get("nickname", "Unknown User") if user_profile else "No User", position="llm_api.chat_with_character()", error_message=f"Error getting chat response: {error}, raw response_text was: {response_text}")
        print(f"ERROR - llm_api.chat_with_character() - Error getting chat response: {error}, raw response_text was: {response_text}\n\n")
    if OPTIONS.get("debug"): # if in debug mode, log this (otherwise, this takes too much time)
        log_other_stuff(username=user_profile.get("nickname", "Unknown User") if user_profile else "No User", position="llm_api.chat_with_character()", log_message=f"Chat response: {response_text}")
    print("LOG - llm_api.chat_with_character() - Chat response: {response_text}\n\n")

    # run refusal check
    try: 
        if api_choice != "ollama": # choose local models without guardrails, so check is not necessary

            refusal_check = create_chat_completion(
                get_analysis_model(),
                [{"role": "user", "content": llm_prompt_library.REFUSAL_CHECK_PROMPT.format(last_turn=response_text)}],
                50,
                temperature=0.7,
            ).lower()
            if OPTIONS.get("debug"): # if in debug mode, log this (otherwise, this takes too much time)
                log_other_stuff(username=user_profile.get("nickname", "Unknown User") if user_profile else "No User", position="llm_api.chat_with_character()", log_message=f"Refusal Check: {refusal_check}")
            print("LOG - llm_api.chat_with_character() - Refusal Check: {refusal_check}\n\n")

            # if model refused to answer in-character, replace response with "Fangtastic filter"
            if refusal_check.startswith("contentrefusal") or refusal_check.endswith("contentrefusal"):
                log_other_stuff(username=user_profile.get("nickname", "Unknown User") if user_profile else "No User", position="llm_api.chat_with_character()", log_message=f"Refusal Check was positive for model {get_analysis_model()}: {refusal_check}")
                print(f"LOG - llm_api.chat_with_character() - Refusal Check was positive for model {get_analysis_model()}: {refusal_check}\n\n")
                return "(Dieser Inhalt wurde gemäß den AGB von Fangtastic automatisch zensiert.)"
        
    except Exception as error:
        log_error(username=user_profile.get("nickname", "Unknown User") if user_profile else "No User", position="llm_api.chat_with_character()", error_message=f"Error during refusal check: {error}, raw refusal_check was: {refusal_check}")
        print(f"ERROR - llm_api.chat_with_character() - Error during refusal check: {error}, raw refusal_check was: {refusal_check}\n\n")
        
    return response_text


def format_chat_history_for_analysis(chat_history: List[Dict[str, str]], message_cap: int = 7) -> str:
    """Format chat history as readable text"""
    formatted = []
    for msg in chat_history[-message_cap:]:
        role = "Spieler" if msg.get("role") == "user" else "Charakter"
        content = msg.get("content", "")
        formatted.append(f"{role}: {content}")
    return "\n".join(formatted)

