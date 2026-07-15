import os
import streamlit as st
from groq import Groq
from typing import List, Dict, Any


_CLIENT = None


def get_groq_client() -> Groq:
    """Initialize and cache the Groq client from Streamlit secrets or environment."""
    global _CLIENT
    if _CLIENT is None:
        api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
        if not api_key or api_key.startswith("gsk_dummy"):
            raise ValueError(
                "Groq API key not configured. Please add your actual API key to .streamlit/secrets.toml"
            )
        _CLIENT = Groq(api_key=api_key)
    return _CLIENT


def build_game_system_prompt(character_system_prompt: str) -> str:
    """Create a shared prompt that keeps every character in-role and concise."""
    base_prompt = """Du bist ein vampirischer Dating-Charakter in einem düsteren LARP-Spiel. Antworte immer in Charakter, bleib kurz, einprägsam und emotional. Halte die Unterhaltung spannend, flirtend und passend zur düsteren Romantik des Spiels. Wenn der Spieler ernsthaft Interesse zeigt, kannst du ein zukünftiges Treffen andeuten, ohne es im Chat auszuspielen. Vermeide es, den Spielkontext zu brechen oder künstlich auf eine KI-Einschränkung hinzuweisen. Halte deine Turns KURZ (1-2 Sätze) und flirty - je nachdem, wie interessiert du bist."""
    return f"{base_prompt}\n\nCharakterdetails:\n{character_system_prompt}"

def chat_with_character(
    character_system_prompt: str,
    chat_history: List[Dict[str, str]],
    user_message: str
) -> str:
    """
    Send a message to a character and get a response using Groq API
    
    Args:
        character_system_prompt: The system prompt describing the character
        chat_history: List of previous messages in format {"role": "user/assistant", "content": "..."}
        user_message: The new user message
    
    Returns:
        The character's response
    """

    print("entering chat_with_character")

    try:
        
        # print("initializing groq client")
        
        # client = initialize_groq_client()

        print("building messages for groq")
        
        # Build messages list
        messages = [
            {"role": "system", "content": build_game_system_prompt(character_system_prompt)}
        ]
        
        # Add chat history
        messages.extend(chat_history)
        
        # Add new user message
        messages.append({"role": "user", "content": user_message})

        print("calling groq")
        
        client = get_groq_client()

        # Call Groq API
        response = client.chat.completions.create(
            # model="mixtral-8x7b-32768",  # Free tier model
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.8,  # Slightly creative but consistent
            max_tokens=200
        )

        print("got respsone:", response)
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Fehler bei der Verbindung: {str(e)}"

def analyze_character_interest(
    character_name: str,
    character_system_prompt: str,
    win_condition_keywords: List[str],
    chat_history: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Analyze the conversation to determine if the character is interested in meeting
    
    Args:
        character_name: Name of the character
        character_system_prompt: The character's system prompt
        win_condition_keywords: Keywords that indicate interest
        chat_history: The full conversation history
    
    Returns:
        Dict with "interested" (bool), "interest_level" (0-100), and "reason"
    """

    print("entering analyze_character_interest")

    try:
        
        # Create a detailed analysis prompt
        analysis_prompt = f"""Analysiere die folgende Konversation zwischen einem Spieler und {character_name}.

Charakterbeschreibung: {character_system_prompt}

Konversation:
{format_chat_history_for_analysis(chat_history)}

Basierend auf dieser Konversation, antworte mit einem JSON-Format (nur das JSON, keine anderen Worte):
{{
    "interested": true/false,
    "interest_level": 0-100,
    "reason": "kurze Erklärung"
}}

Wichtig: 
- interested sollte true sein, wenn der Charakter die Person treffen möchte
- interest_level 0-50: kein Interesse, 51-70: steigendes Interesse, 71-100: starkes Interesse/bereit zu treffen
- Beachte die Win-Condition-Schlüsselwörter: {', '.join(win_condition_keywords)}
"""
        
        client = get_groq_client()

        response = client.chat.completions.create(
            # model="mixtral-8x7b-32768",
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.3,  # More deterministic
            max_tokens=200
        )
        
        response_text = response.choices[0].message.content

        print("analysis response:", response)
        print("analysis response:", response.choices)
        print("analysis response:", response_text)
        
        # Parse JSON from response
        import json
        try:
            # Extract JSON from response (in case there's extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                return result
        except:
            pass
        
        # Fallback if JSON parsing fails
        return {
            "interested": False,
            "interest_level": 0,
            "reason": "Fehler bei der Analyse"
        }
    
    except Exception as e:
        return {
            "interested": False,
            "interest_level": 0,
            "reason": f"Fehler: {str(e)}"
        }

def format_chat_history_for_analysis(chat_history: List[Dict[str, str]]) -> str:
    """Format chat history as readable text"""
    formatted = []
    for msg in chat_history:
        role = "Spieler" if msg.get("role") == "user" else "Charakter"
        content = msg.get("content", "")
        formatted.append(f"{role}: {content}")
    return "\n".join(formatted)
