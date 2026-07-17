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


def build_game_system_prompt(character_system_prompt: str, interest_analysis: Dict[str, Any]) -> str:
    """Create a shared prompt that keeps every character in-role and concise."""
    base_prompt = """Du bist ein Charakter in einem düsteren Vampir-Rollenspiel und du schreibst über eine simulierte Online-Dating-Plattform mit einer anderen Figur, die sich für dich interessiert. Antworte immer in Charakter, fasse dich sehr kurz (1-2 Sätze), aber halte die Unterhaltung spannend, flirtend und passend zur düsteren Romantik des Spiels. Wenn dein Gegenüber ernsthaft Interesse zeigt, und du dieses Interesse erwiderst, kannst du ein Treffen vorschlagen - danach kannst du weiter Smalltalk treiben, aber erinnere dich daran, dass dies ein Online-Chat ist und ihr bald ein Offline-Treffen habt. Vermeide es, den Spielkontext zu brechen oder künstlich auf KI hinzuweisen. Wenn du einen Treffpunkt für einen Ort nennst, halt ihn realistisch und passend zu Berlin: Keine "alte Villa am Waldrand", sondern "die kleine Eckkneipe am Kurt-Schumacher-Platz, du erkennst mich an der roten Mütze" oder etwas Vergleichbares, was zu deinem Charakter passt."""
    return f"{base_prompt}\n\nCharakterdetails:\n{character_system_prompt}\n\nLetzte Analyse des Interesses, das dein Charakter am Gegenüber hat:\n{interest_analysis}"

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
        
        # Build messages list
        messages = [
            {"role": "system", "content": build_game_system_prompt(character_system_prompt, interest_analysis)}
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
    interest_analysis: Dict[str, Any],
    chat_history: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Analyze the conversation to determine if the character is interested in meeting
    
    Args:
        character_name: Name of the character
        character_system_prompt: The character's system prompt
        interest_analysis: Recent analysis of the character's interest level
        chat_history: The full conversation history
    
    Returns:
        Dict with "interested" (bool), "interest_level" (0-100), and "reason"
    """

    print("entering analyze_character_interest")

    try:
        
        # Create a detailed analysis prompt
        # TODO the characters are still swayed way too easily by the player, 
        # need to make them a slower burn, less likely to be meeting after a single message. 
        # Also, the interest level should not jump more than 10-15 points per turn, 
        # to simulate a more realistic progression of interest.
        # This is currently not followed despite being a part of the prompt.
        # Maybe the two-step process of first doing the chat 
        # and then analyzing interest is too complex? Or not complex enoough? 
        # Maybe the model is just too eager to please the player.
        analysis_prompt = f"""Analysiere die folgende simulierte Dating-Konversation zwischen einem Vampir-Spieler und der fiktiven Figur {character_name}.

Charakterbeschreibung: {character_system_prompt}

Konversation:
{format_chat_history_for_analysis(chat_history)}

Letzte Analyse des Interesses, das dein Charakter am Gegenüber hat:
{interest_analysis}

Basierend auf dieser Konversation, antworte mit einem JSON-Format (nur das JSON, keine anderen Worte):
{{
    "meeting_planned": true/false,
    "interest_level": 0-100,
    "reason": "kurze Erklärung"
}}

Wichtig: 
- meeting_planned sollte ERST und NUR dann true sein, wenn der Charakter ein Interesse über 85 und im Gespräch ein Treffen geplant hat, ansonsten IMMER false
- interest_level sollte sich pro Turn immer nur um bis zu 15 Punkte ändern, um die Entwicklung des Interesses zu simulieren
- Level: 0-30: Charakter weiß noch nicht, was vom Gegenüber zu halten ist, 30-50: Charakter ist etwas interessiert oder findet das Gespräch bisher nett, 50-70: Charakter ist interessiert und möchte sein Gegenüber kennen lernen, 70-85: Charakter ist unterhalten oder fasziniert, will das Gespräch aufrecht erhalten, 85-100: starkes Interesse, Charakter ist bereit sich im echten Leben zu treffen
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

        # print("analysis response:", response)
        # print("analysis response:", response.choices)
        # print("analysis response:", response_text)
        
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
