"""OpenRouter adapter implementing the shared chat and dialog-management API."""

import json
import os
import re
from typing import Any, Dict, List

import requests
import streamlit as st

import prompt_library
from fangtastic_options import OPTIONS


OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"

# OpenRouter model names, selected from https://openrouter.ai/models
# "openrouter_chat_model": "openai/gpt-4o-mini",
# "openrouter_analysis_model": "openai/gpt-4o-mini",

# TODO experiment with models, smarter handling
open_router_analysis_model = "qwen/qwen3.8-27b:free"
open_router_chat_model = "qwen/qwen3.8-27b:free"

def _get_api_key() -> str:
    api_key = st.secrets.get("OPEN_ROUTER_API_KEY", os.getenv("OPEN_ROUTER_API_KEY", ""))
    return api_key


def _create_completion(model: str, messages: List[Dict[str, str]], max_tokens: int | None = None,
                       temperature: float | None = None) -> str:
    payload: Dict[str, Any] = {
        "model": model,
        "max_tokens": 150,
        "messages": messages,
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    response = requests.post(
        OPENROUTER_CHAT_COMPLETIONS_URL,
        headers={
            "Authorization": f"Bearer {_get_api_key()}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"].get("content", "") or ""


def format_chat_history_for_analysis(chat_history: List[Dict[str, str]]) -> str:
    formatted = []
    for msg in chat_history[-7:]:
        role = "Spieler" if msg.get("role") == "user" else "Charakter"
        formatted.append(f"{role}: {msg.get('content', '')}")
    return "\n".join(formatted)


def manage_dialog(
    character_name: str,
    character_strategy: str,
    previous_state: Dict[str, Any],
    chat_history: List[Dict[str, str]],
    user_profile: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    previous_level = int(previous_state.get("interest_level", 0))
    previous_meeting = bool(previous_state.get("meeting_planned", False))
    previous_blocked = bool(previous_state.get("user_blocked", False))

    if not chat_history or len(chat_history) < 2:
        return {
            "meeting_planned": False,
            "interest_level": previous_level,
            "user_blocked": False,
            "reason": "Noch keine Nachricht.",
            "char_instructions": "",
        }

    latest_text = str(chat_history[-1].get("content", "")).strip()
    if not latest_text:
        return {
            "meeting_planned": previous_meeting,
            "interest_level": previous_level,
            "user_blocked": False,
            "reason": "",
            "char_instructions": "",
        }

    prompt = prompt_library.DIALOG_MANAGEMENT_PROMPT.format(
        character_name=character_name,
        conversation_summary=format_chat_history_for_analysis(chat_history),
        character_strategy=character_strategy,
        user_profile=prompt_library.USER_PROFILE_CONTEXT.format(
            nickname=(user_profile or {}).get("nickname", ""),
            age=(user_profile or {}).get("age", ""),
            gender=(user_profile or {}).get("gender", ""),
            interests=", ".join((user_profile or {}).get("interests", [])),
            looking_for=", ".join((user_profile or {}).get("looking_for", [])),
            bio=(user_profile or {}).get("bio", ""),
        ),
        previous_state_json=json.dumps(previous_state, ensure_ascii=False),
    )

    try:
        
        response_text = _create_completion(open_router_analysis_model, [{"role": "user", "content": prompt}], 180)
        print("Analysis response:", response_text)
        print()

        match = re.search(r"\{.*\}", response_text, re.S)
        if match:
            parsed = json.loads(match.group(0))
            interest_level = min(100, max(0, int(parsed.get("interest_level", previous_level))))
            delta = interest_level - previous_level
            if abs(delta) > 15:
                interest_level = previous_level + max(-15, min(15, delta))
            return {
                "meeting_planned": bool(parsed.get("meeting_planned", False)),
                "interest_level": interest_level,
                "user_blocked": bool(parsed.get("user_blocked", False)),
                "reason": str(parsed.get("reason", ""))[:160],
                "char_instructions": str(parsed.get("char_instructions", "")),
            }
        return {
            "meeting_planned": previous_meeting,
            "interest_level": previous_level,
            "user_blocked": previous_blocked,
            "reason": "Kein JSON, nur: " + response_text,
            "char_instructions": "",
        }
    except Exception as error:
        return {
            "meeting_planned": False,
            "interest_level": previous_level,
            "user_blocked": previous_blocked,
            "reason": f"Fehler: {str(error)[:140]}",
            "char_instructions": "",
        }


def chat_with_character(
    character_description: str,
    current_time: str,
    username: str,
    chat_history: List[Dict[str, str]],
    management_result: Dict[str, Any],
    user_message: str,
    user_profile: Dict[str, Any] | None = None,
) -> str:
    
    char_system_prompt = prompt_library.CHARACTER_REPLY_PROMPT.format(
        current_time=current_time,
        character_description=character_description,
        username=username,
        user_profile=prompt_library.USER_PROFILE_CONTEXT.format(
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
    messages.append({"role": "user", "content": user_message})
    messages.append({
        "role": "user",
        "content": "system_prompt-Ergänzung. In deinem nächsten Turn: "
        + str(management_result.get("char_instructions", "")),
    })

    try:

        answer = _create_completion(open_router_chat_model, messages, 250, temperature=0.8)
        print("chat response:", answer)
        print()

        refusal_check = _create_completion(
            open_router_analysis_model,
            [{"role": "user", "content": prompt_library.REFUSAL_CHECK_PROMPT.format(last_turn=answer)}],
            50,
            temperature=1,
        ).lower()
        print("refusal check response:", refusal_check)
        print()
        if refusal_check.startswith("contentrefusal") or refusal_check.endswith("contentrefusal"):
            return "(Dieser Inhalt wurde gemäß den AGB von Fangtastic automatisch zensiert.)"

        return answer
    
    except Exception as error:
        return f"Fehler bei der Verbindung: {str(error)}"