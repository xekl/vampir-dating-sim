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


chat_model_index = -1
analysis_model_index = -1 

def get_next_groq_chat_model():

    global chat_model_index

    groq_chat_models = [
        # see https://console.groq.com/docs/rate-limits
        "groq/compound", # Default model for character chat
        "llama-3.3-70b-versatile",
        "meta-llama/llama-prompt-guard-2-86m",
        "openai/gpt-oss-120b",
        "qwen/qwen3.6-27b",
        "meta-llama/llama-prompt-guard-2-22m",
        "openai/gpt-oss-20b",
        "llama-3.1-8b-instant"
    ]
    chat_model_index = (chat_model_index + 1) % len(groq_chat_models)
    return groq_chat_models[chat_model_index]

def get_next_groq_analysis_model():

    global analysis_model_index

    groq_analysis_models = [
        "llama-3.1-8b-instant",
        "openai/gpt-oss-20b", # does reasoning and fills up max tokens with it ...
        "qwen/qwen3.6-27b",
    ]

    analysis_model_index = (analysis_model_index + 1) % len(groq_analysis_models)
    return groq_analysis_models[analysis_model_index]


groq_chat_model = get_next_groq_chat_model()
groq_analysis_model = get_next_groq_analysis_model()


def chat_with_character(
    character_system_prompt: str,
    current_time: str,
    username: str,
    chat_history: List[Dict[str, str]],
    management_result: Dict[str, Any],
    user_message: str
) -> str:
    """
    Send a message to a character and get a response using Groq API
    
    Args:
        character_system_prompt: The system prompt describing the character
        username: The username of the player
        chat_history: List of previous messages in format {"role": "user/assistant", "content": "..."}
        management_result: Recent analysis of the dialog flow and character's interest level
        user_message: The new user message
    
    Returns:
        The character's response
    """

    print("entering chat_with_character")
    global groq_chat_model

    try:
        
        # Build system prompt
        char_system_prompt = prompt_library.CHARACTER_REPLY_PROMPT.format(
            current_time = current_time,
            character_system_prompt = character_system_prompt,
            username = username,
            next_turn_instructions = management_result.get("char_instructions")
            # interest_analysis_json = json.dumps(interest_analysis, ensure_ascii=False),
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
            # model="llama-3.3-70b-versatile",
            model=groq_chat_model,
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
            # Switch to the next model in the list and retry
            groq_chat_model = get_next_groq_chat_model()
            return chat_with_character(character_system_prompt, username, chat_history, management_result, user_message)
            # TODO handle model or groq api key switch 
            # then recall this function with same parameters
            # for now, return error
            # return f"Rate limit reached for model {rate_limit_error_model}."
        return f"Fehler bei der Verbindung: {str(e)}"


def manage_dialog(
    character_name: str,
    character_system_prompt: str,
    previous_state: Dict[str, Any],
    chat_history: List[Dict[str, str]],
    ) -> Dict[str, Any]:

    global groq_analysis_model

    previous_level = int(previous_state.get("interest_level", 0))
    previous_meeting = bool(previous_state.get("meeting_planned", False))

    if not chat_history or len(chat_history) == 1:
        return {
            "meeting_planned": False,
            "interest_level": previous_level,
            "reason": "Noch keine Nachricht.",
            "char_instructions": "",
        }

    latest_turn = chat_history[-1]
    latest_text = str(latest_turn.get("content", "")).strip()
    if not latest_text:
        return {
            "meeting_planned": previous_meeting,
            "interest_level": previous_level,
            "reason": "Leere Nachricht ignoriert.",
            "char_instructions": "",
        }

    conversation_summary = format_chat_history_for_analysis(chat_history)

    prompt = prompt_library.DIALOG_MANAGEMENT_PROMPT.format(
        character_name = character_name,
        character_system_prompt = character_system_prompt,
        conversation_summary = conversation_summary,
        previous_state_json = json.dumps(previous_state, ensure_ascii=False),
    )
    
    try:

        print("Managing dialog with model:", groq_analysis_model)

        response = groq_client.chat.completions.create(
            model=groq_analysis_model,
            messages=[{"role": "user", "content": prompt}],
            # temperature=0.2,
            max_tokens=180,
        )
        response_text = response.choices[0].message.content

        print("Interest analysis response:", response, response_text)

        match = re.search(r"\{.*\}", response_text, re.S) # find JSON object in the response
        if match:
            parsed = json.loads(match.group(0))
            interest_level = int(parsed.get("interest_level", previous_level))
            interest_level = min(100, max(0, interest_level))
            # if previous_meeting:
            #     interest_level = max(interest_level, previous_level)
            delta = interest_level - previous_level
            if abs(delta) > 15:
                interest_level = previous_level + max(-15, min(15, delta))
            meeting_planned = bool(parsed.get("meeting_planned", False)) # and interest_level >= 85 and len(chat_history) >= 4
            char_instructions = str(parsed.get("char_instructions", ""))
            return {
                "meeting_planned": meeting_planned,
                "interest_level": interest_level,
                "reason": str(parsed.get("reason", ""))[:160],
                "char_instructions": char_instructions,
            }
        
        else: # no JSON found, return previous state
            return {
            "meeting_planned": previous_meeting,
            "interest_level": previous_level,
            "reason": "Message contains no JSON, was: " + response_text,
            "char_instructions": "",
        }

    except Exception as e:
        # Catch Rate Limit error for workarounds 
        rate_limit_error_model = str(e).split("Rate limit reached for model `")[1].split("`")[0] if "Rate limit reached for model" in str(e) else None
        if rate_limit_error_model:
            # Switch to the next model in the list and retry
            groq_analysis_model = get_next_groq_analysis_model()
            return manage_dialog(character_name, character_system_prompt, previous_state, chat_history)
            # TODO handle model or groq api key switch 
            # then recall this function with same parameters
            # for now, return error
            # return f"Rate limit reached for model {rate_limit_error_model}."
        # return f"Fehler bei der Verbindung: {str(e)}"

        return {
            "meeting_planned": False,
            "interest_level": previous_level,
            "reason": "Fehler bei der Analyse: " + {str(e)},
            "char_instructions": "",
        }




# def analyze_character_interest(
#     character_name: str,
#     character_system_prompt: str,
#     previous_state: Dict[str, Any],
#     chat_history: List[Dict[str, str]],
# ) -> Dict[str, Any]:
#     """Derive a more believable interest progression from the conversation history."""

#     global groq_analysis_model

#     previous_level = int(previous_state.get("interest_level", 0))
#     previous_meeting = bool(previous_state.get("meeting_planned", False))

#     if not chat_history:
#         return {
#             "meeting_planned": False,
#             "interest_level": previous_level,
#             "reason": "Noch keine neue Nachricht.",
#         }

#     latest_turn = chat_history[-1]
#     latest_text = str(latest_turn.get("content", "")).strip()
#     if not latest_text:
#         return {
#             "meeting_planned": previous_meeting,
#             "interest_level": previous_level,
#             "reason": "Leere Nachricht ignoriert.",
#         }

#     conversation_summary = format_chat_history_for_analysis(chat_history)

#     prompt = prompt_library.INTEREST_ANALYSIS_PROMPT_TEMPLATE.format(
#         character_name = character_name,
#         character_system_prompt = character_system_prompt,
#         conversation_summary = conversation_summary,
#         previous_state_json = json.dumps(previous_state, ensure_ascii=False),
#     )
    
#     try:

#         print("Analyzing interest with model:", groq_analysis_model)

#         response = groq_client.chat.completions.create(
#             model=groq_analysis_model,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.2,
#             max_tokens=180,
#         )
#         response_text = response.choices[0].message.content

#         print("Interest analysis response:", response, response_text)

#         match = re.search(r"\{.*\}", response_text, re.S) # find JSON object in the response
#         if match:
#             parsed = json.loads(match.group(0))
#             interest_level = int(parsed.get("interest_level", previous_level))
#             interest_level = min(100, max(0, interest_level))
#             if previous_meeting:
#                 interest_level = max(interest_level, previous_level)
#             delta = interest_level - previous_level
#             if abs(delta) > 15:
#                 interest_level = previous_level + max(-15, min(15, delta))
#             meeting_planned = bool(parsed.get("meeting_planned", False)) and interest_level >= 85 and len(chat_history) >= 4
#             return {
#                 "meeting_planned": meeting_planned,
#                 "interest_level": interest_level,
#                 "reason": str(parsed.get("reason", ""))[:160],
#             }
        
#         else: # no JSON found, return previous state
#             return {
#             "meeting_planned": previous_meeting,
#             "interest_level": previous_level,
#             "reason": "Message contains no JSON, was: " + response_text,
#         }

#     except Exception as e:
#         # Catch Rate Limit error for workarounds 
#         rate_limit_error_model = str(e).split("Rate limit reached for model `")[1].split("`")[0] if "Rate limit reached for model" in str(e) else None
#         if rate_limit_error_model:
#             # Switch to the next model in the list and retry
#             groq_analysis_model = get_next_groq_analysis_model()
#             return analyze_character_interest(character_name, character_system_prompt, previous_state, chat_history)
#             # TODO handle model or groq api key switch 
#             # then recall this function with same parameters
#             # for now, return error
#             # return f"Rate limit reached for model {rate_limit_error_model}."
#         # return f"Fehler bei der Verbindung: {str(e)}"

#         return {
#             "meeting_planned": False,
#             "interest_level": interest_level,
#             "reason": "Fehler bei der Analyse: " + {str(e)},
#         }


def format_chat_history_for_analysis(chat_history: List[Dict[str, str]]) -> str:
    """Format chat history as readable text"""
    formatted = []
    for msg in chat_history:
        role = "Spieler" if msg.get("role") == "user" else "Charakter"
        content = msg.get("content", "")
        formatted.append(f"{role}: {content}")
    return "\n".join(formatted)
