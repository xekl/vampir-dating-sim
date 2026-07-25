import json
import os
import re
from typing import Any, Dict, List

import streamlit as st
from groq import Groq

import prompt_library


api_key_index = -1
last_api_key_reached = 0
chat_model_index = -1
analysis_model_index = -1 


def get_next_groq_client():

    global api_key_index
    global last_api_key_reached

    api_keys = [st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", "")), 
                st.secrets.get("GROQ_API_KEY_2", os.getenv("GROQ_API_KEY_2", "")), 
                st.secrets.get("GROQ_API_KEY_3", os.getenv("GROQ_API_KEY_3", "")),
                st.secrets.get("GROQ_API_KEY_4", os.getenv("GROQ_API_KEY_4", "")),
                st.secrets.get("GROQ_API_KEY_5", os.getenv("GROQ_API_KEY_5", "")),
                st.secrets.get("GROQ_API_KEY_6", os.getenv("GROQ_API_KEY_6", "")),
                st.secrets.get("GROQ_API_KEY_7", os.getenv("GROQ_API_KEY_7", "")),
                st.secrets.get("GROQ_API_KEY_8", os.getenv("GROQ_API_KEY_8", "")),
                st.secrets.get("GROQ_API_KEY_9", os.getenv("GROQ_API_KEY_9", "")),
                st.secrets.get("GROQ_API_KEY_10", os.getenv("GROQ_API_KEY_10", "")),
                ]
    
    if api_key_index + 1 == len(api_keys):
        last_api_key_reached += 1
    
    api_key_index = (api_key_index + 1) % len(api_keys)
    return Groq(api_key=api_keys[api_key_index]) 

def get_next_groq_chat_model():

    global chat_model_index

    groq_chat_models = [
        # see https://console.groq.com/docs/rate-limits
        "llama-3.3-70b-versatile", # smartest chatter so far
        # "openai/gpt-oss-120b", # refuses to arrange meetings
        # "openai/gpt-oss-20b",
        # "openai/gpt-oss-safeguard-20b", 
        "qwen/qwen3.6-27b",
        "llama-3.1-8b-instant",
        "groq/compound", # not great at following instructions BUT HAS NO LIMIT
    ]
    chat_model_index = (chat_model_index + 1) % len(groq_chat_models)
    return groq_chat_models[chat_model_index]

def get_next_groq_analysis_model():

    global analysis_model_index

    groq_analysis_models = [
        # "llama-3.3-70b-versatile", # also smartest reasoner
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b", 
        # "openai/gpt-oss-safeguard-20b", 
        "qwen/qwen3.6-27b", 
        "llama-3.1-8b-instant",
        "groq/compound", # not great at following instructions BUT HAS NO LIMIT
    ]

    analysis_model_index = (analysis_model_index + 1) % len(groq_analysis_models)
    return groq_analysis_models[analysis_model_index]


groq_client = get_next_groq_client()
groq_chat_model = get_next_groq_chat_model()
groq_analysis_model = get_next_groq_analysis_model()


def format_chat_history_for_analysis(chat_history: List[Dict[str, str]]) -> str:
    """Format chat history as readable text"""
    formatted = []
    message_cap = 7 # max messages to include
    for msg in chat_history[-message_cap:]:
        role = "Spieler" if msg.get("role") == "user" else "Charakter"
        content = msg.get("content", "")
        formatted.append(f"{role}: {content}")
    return "\n".join(formatted)


def manage_dialog(
    character_name: str,
    character_strategy: str,
    previous_state: Dict[str, Any],
    chat_history: List[Dict[str, str]],
    ) -> Dict[str, Any]:

    global groq_client
    global groq_analysis_model
    global last_api_key_reached

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

    latest_turn = chat_history[-1]
    latest_text = str(latest_turn.get("content", "")).strip()
    if not latest_text:
        return {
            "meeting_planned": previous_meeting,
            "interest_level": previous_level,
            "user_blocked": False,
            "reason": "",
            "char_instructions": "",
        }

    conversation_summary = format_chat_history_for_analysis(chat_history)

    prompt = prompt_library.DIALOG_MANAGEMENT_PROMPT.format(
        character_name = character_name,
        conversation_summary = conversation_summary,
        character_strategy = character_strategy,
        previous_state_json = json.dumps(previous_state, ensure_ascii=False),
    )
    
    try:

        print("Managing dialog with model:", groq_analysis_model)
        print()
        # print("prompt:", prompt)
        # print()

        # Call groq API
        temperature = None
        max_tokens = 180
        if "gpt-oss" in groq_analysis_model:
            response = groq_client.chat.completions.create(
                model=groq_analysis_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={"reasoning_effort": "low"}
            )
        elif "qwen" in groq_analysis_model:
            response = groq_client.chat.completions.create(
                model=groq_analysis_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={"reasoning_effort": "none"}
            ) 
        else:
            response = groq_client.chat.completions.create(
                model=groq_analysis_model,
                messages=[{"role": "user", "content": prompt}],
                # temperature=0.2,
                max_tokens=180,
            )
        response_text = response.choices[0].message.content

        print("Analysis response:", response, response_text)
        print()

        match = re.search(r"\{.*\}", response_text, re.S) # find JSON object in the response
        if match:
            parsed = json.loads(match.group(0))
            interest_level = int(parsed.get("interest_level", previous_level))
            interest_level = min(100, max(0, interest_level))
            delta = interest_level - previous_level
            if abs(delta) > 15:
                interest_level = previous_level + max(-15, min(15, delta))
            meeting_planned = bool(parsed.get("meeting_planned", False)) # and interest_level >= 85 and len(chat_history) >= 4
            user_blocked = bool(parsed.get("user_blocked", False)) 
            char_instructions = str(parsed.get("char_instructions", ""))
            return {
                "meeting_planned": meeting_planned,
                "interest_level": interest_level,
                "user_blocked": user_blocked,
                "reason": str(parsed.get("reason", ""))[:160],
                "char_instructions": char_instructions,
            }
        
        else: # no JSON found, return previous state
            return {
            "meeting_planned": previous_meeting,
            "interest_level": previous_level,
            "user_blocked": previous_blocked,
            "reason": "Kein JSON, nur: " + response_text,
            "char_instructions": "",
        }

    except Exception as e:

        # Catch Rate Limit error for workarounds 
        rate_limit_error_model = str(e).split("Rate limit reached for model `")[1].split("`")[0] if "Rate limit reached for model" in str(e) else None
        if rate_limit_error_model:

            # Switch to the next API key and retry with a new client 
            print("rate limit reached for model, switching to API key", api_key_index+1)
            print()
            groq_client = get_next_groq_client()

            # But if you are just recursing through the keys now, also switch model 
            if last_api_key_reached > 3: 
                groq_analysis_model = get_next_groq_analysis_model()
                last_api_key_reached = 0 # and reset key recursion check

            return manage_dialog(character_name, character_strategy, previous_state, chat_history)

        print("error: ", e)

        return {
            "meeting_planned": False,
            "interest_level": previous_level,
            "user_blocked": previous_blocked,
            "reason": "...",
            "char_instructions": "",
        }



def chat_with_character(
    character_description: str,
    current_time: str,
    username: str,
    chat_history: List[Dict[str, str]],
    management_result: Dict[str, Any],
    user_message: str
) -> str:
    """
    Send a message to a character and get a response using Groq API
    
    Args:
        character_description: The system prompt describing the character
        username: The username of the player
        chat_history: List of previous messages in format {"role": "user/assistant", "content": "..."}
        management_result: Recent analysis of the dialog flow and character's interest level
        user_message: The new user message
    
    Returns:
        The character's response
    """

    global groq_client
    global groq_chat_model
    global last_api_key_reached

    print("entering chat_with_character with model:", groq_chat_model)
    print()

    try:
        
        # Build system prompt
        char_system_prompt = prompt_library.CHARACTER_REPLY_PROMPT.format(
            current_time = current_time,
            character_description = character_description,
            username = username,
            # next_turn_instructions = management_result.get("char_instructions")
            # interest_analysis_json = json.dumps(interest_analysis, ensure_ascii=False),
        )
        messages = [
            {"role": "system", "content": char_system_prompt}
        ]

        # print("char_system_prompt:", char_system_prompt)
        # print()

        # Add chat history
        messages.extend(chat_history)
        
        # Add new user message
        messages.append({"role": "user", "content": user_message})

        # Add next turn instructions
        next_turn_instructions = management_result.get("char_instructions")
        messages.append({"role": "user", "content": "system_prompt-Ergänzung. In deinem nächsten Turn: " + next_turn_instructions})
        
        # Call Groq API
        temperature = 0.8
        max_tokens = 250
        if "gpt-oss" in groq_chat_model:
            response = groq_client.chat.completions.create(
                model=groq_chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={"reasoning_effort": "low"}
            )
        elif "qwen" in groq_chat_model:
            response = groq_client.chat.completions.create(
                model=groq_chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={"reasoning_effort": "none"}
            )
        else:
            response = groq_client.chat.completions.create(
                model=groq_chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        print("chat response:", response)
        print()

        # refusal filter: if model refuses, overwrite answer with fake Fangtastic blocker
        check_refusal_messages = [
            {"role": "user", "content": prompt_library.REFUSAL_CHECK_PROMPT.format(last_turn = response)}
        ]
        is_refusal = groq_client.chat.completions.create(
                model="groq/compound", # you can do this, compound!
                messages=check_refusal_messages,
                temperature=1,
                max_tokens=50,
            )
        print("refusal check response:", is_refusal)
        print()
        if is_refusal.choices[0].message.content.lower().startswith("contentrefusal") or is_refusal.choices[0].message.content.lower().endswith("contentrefusal"):
            return "(Dieser Inhalt wurde gemäß den AGB von Fangtastic automatisch zensiert.)"
        
        # final response if no refusal
        if "compound" in groq_chat_model: 
            return response.choices[0].message.reasoning # hack for compound model: reasoning answer usually better than actual answer ...
        else: 
            return response.choices[0].message.content
    
    except Exception as e:
        # Catch Rate Limit error for workarounds 
        rate_limit_error_model = str(e).split("Rate limit reached for model `")[1].split("`")[0] if "Rate limit reached for model" in str(e) else None
        if rate_limit_error_model:

            # Switch to the next API key and retry with a new client 
            print("rate limit reached for model, switching to API key", api_key_index+1)
            print()
            groq_client = get_next_groq_client()

            # But if you are just recursing through the keys now, also switch model 
            if last_api_key_reached > 3: 
                groq_chat_model = get_next_groq_chat_model()
                last_api_key_reached = 0 # and reset key recursion check

            return chat_with_character(character_description, current_time, username, chat_history, management_result, user_message)

        return f"Fehler bei der Verbindung: {str(e)}"
