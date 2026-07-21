import json
import os
import re
from typing import Any, Dict, List

import streamlit as st
from groq import Groq

import prompt_library

groq_client = None
api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
if not api_key or api_key.startswith("gsk_dummy"):
    raise ValueError(
        "Groq API key not configured. Please add your actual API key to .streamlit/secrets.toml"
    )
groq_client = Groq(api_key=api_key)


def chat_with_character(
    character_system_prompt: str,
    chat_history: List[Dict[str, str]],
    interest_analysis: Dict[str, Any],
    user_message: str
) -> str:
    """
    Send a message to a character and get a response using Groq API
    
    Args:
        character_system_prompt: The system prompt describing the character
        chat_history: List of previous messages in format {"role": "user/assistant", "content": "..."}
        interest_analysis: Recent analysis of the character's interest level
        user_message: The new user message
    
    Returns:
        The character's response
    """

    print("entering chat_with_character")

    try:
        
        # Build system prompt
        char_system_prompt = prompt_library.CHARACTER_REPLY_PROMPT_TEMPLATE.format(
            base_prompt = prompt_library.CHARACTER_REPLY_PROMPT_BASE,
            character_system_prompt = character_system_prompt,
            interest_analysis_json = json.dumps(interest_analysis, ensure_ascii=False),
        )
        messages = [
            {"role": "system", "content": char_system_prompt}
        ]

        # Add chat history
        messages.extend(chat_history)
        
        # Add new user message
        messages.append({"role": "user", "content": user_message})

        print("calling groq")
        
        # Call Groq API
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            # model="mixtral-8x7b-32768",
            messages=messages,
            temperature=0.8,  # Slightly creative but consistent
            max_tokens=200
        )

        print("got respsone:", response)
        
        return response.choices[0].message.content
    
    except Exception as e:
        # Catch Rate Limit error for workarounds 
        rate_limit_error_model = str(e).split("Rate limit reached for model `")[1].split("`")[0] if "Rate limit reached for model" in str(e) else None
        if rate_limit_error_model:
            print("---- Rate limit reached for model", rate_limit_error_model)
            # TODO handle model or groq api key switch 
            # then recall this function with same parameters
            # for now, return error
            return f"Rate limit reached for model {rate_limit_error_model}."
        return f"Fehler bei der Verbindung: {str(e)}"


def analyze_character_interest(
    character_name: str,
    character_system_prompt: str,
    previous_state: Dict[str, Any],
    chat_history: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Derive a more believable interest progression from the conversation history."""
    previous_level = int(previous_state.get("interest_level", 0))
    previous_meeting = bool(previous_state.get("meeting_planned", False))

    if not chat_history:
        return {
            "meeting_planned": False,
            "interest_level": previous_level,
            "reason": "Noch keine neue Nachricht.",
        }

    latest_turn = chat_history[-1]
    latest_text = str(latest_turn.get("content", "")).strip()
    if not latest_text:
        return {
            "meeting_planned": previous_meeting,
            "interest_level": previous_level,
            "reason": "Leere Nachricht ignoriert.",
        }

    conversation_summary = format_chat_history_for_analysis(chat_history)

    prompt = prompt_library.INTEREST_ANALYSIS_PROMPT_TEMPLATE.format(
        character_name = character_name,
        character_system_prompt = character_system_prompt,
        conversation_summary = conversation_summary,
        previous_state_json = json.dumps(previous_state, ensure_ascii=False),
    )
    
    try:
        response = groq_client.chat.completions.create(
            # model="llama-3.3-70b-versatile",
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=180,
        )
        response_text = response.choices[0].message.content

        print("Interest analysis response:", response_text)

        match = re.search(r"\{.*\}", response_text, re.S) # find JSON object in the response
        if match:
            parsed = json.loads(match.group(0))
            interest_level = int(parsed.get("interest_level", previous_level))
            interest_level = min(100, max(0, interest_level))
            if previous_meeting:
                interest_level = max(interest_level, previous_level)
            delta = interest_level - previous_level
            if abs(delta) > 15:
                interest_level = previous_level + max(-15, min(15, delta))
            meeting_planned = bool(parsed.get("meeting_planned", False)) and interest_level >= 85 and len(chat_history) >= 4
            return {
                "meeting_planned": meeting_planned,
                "interest_level": interest_level,
                "reason": str(parsed.get("reason", ""))[:160],
            }
        
        else: # no JSON found, return previous state
            interest_level = previous_level

    except Exception as e:
        # Catch Rate Limit error for workarounds 
        rate_limit_error_model = str(e).split("Rate limit reached for model `")[1].split("`")[0] if "Rate limit reached for model" in str(e) else None
        if rate_limit_error_model:
            print("---- Rate limit reached for model", rate_limit_error_model)
            # TODO handle model or groq api key switch 
            # then recall this function with same parameters
            # for now, return error
            return f"Rate limit reached for model {rate_limit_error_model}."
        return f"Fehler bei der Verbindung: {str(e)}"

    return {
        "meeting_planned": False,
        "interest_level": interest_level,
        "reason": "Fehler bei der Analyse, vorheriger Zustand beibehalten.",
    }


def format_chat_history_for_analysis(chat_history: List[Dict[str, str]]) -> str:
    """Format chat history as readable text"""
    formatted = []
    for msg in chat_history:
        role = "Spieler" if msg.get("role") == "user" else "Charakter"
        content = msg.get("content", "")
        formatted.append(f"{role}: {content}")
    return "\n".join(formatted)
