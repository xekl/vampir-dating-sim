import json
import re 
import os
import streamlit as st
from groq import Groq
from typing import List, Dict, Any


groq_client = None
api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
if not api_key or api_key.startswith("gsk_dummy"):
    raise ValueError(
        "Groq API key not configured. Please add your actual API key to .streamlit/secrets.toml"
    )
groq_client = Groq(api_key=api_key)


def build_game_system_prompt(character_system_prompt: str, interest_analysis: Dict[str, Any]) -> str:
    """Create a shared prompt that keeps every character in-role and concise."""
    base_prompt = """Du bist ein Charakter in einem düsteren Vampir-Rollenspiel und du schreibst über eine simulierte Online-Dating-Plattform mit einer anderen Figur, die sich für dich interessiert. Antworte immer in Charakter, fasse dich sehr kurz (1-2 Sätze), aber halte die Unterhaltung spannend, flirtend und passend zur düsteren Romantik des Spiels. Sei zunächst vorsichtig und langsam, nicht sofort zu offen. Ein echtes Treffen soll erst nach mehreren Gesprächen oder einer klaren emotionalen/konkreten Einladung passieren. Vermeide es, den Spielkontext zu brechen oder künstlich auf KI hinzuweisen. Wenn du einen Treffpunkt für einen Ort nennst, halt ihn realistisch und passend zu Berlin: Keine "alte Villa am Waldrand", sondern "die kleine Eckkneipe am Kurt-Schumacher-Platz, du erkennst mich an der roten Mütze" oder etwas Vergleichbares, das zu deinem Charakter passt."""
    return f"{base_prompt}\n\nCharakterdetails:\n{character_system_prompt}\n\nLetzte Interesse-Analyse:\n{json.dumps(interest_analysis, ensure_ascii=False)}"

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
        
        # Call Groq API
        response = groq_client.chat.completions.create(
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
    prompt = f"""Analysiere die folgende simulierte Dating-Konversation zwischen einem Vampir-Spieler und der fiktiven Figur {character_name}.

Charakterbeschreibung: {character_system_prompt}

Konversation:
{conversation_summary}

Vorheriger Zustand:
{json.dumps(previous_state, ensure_ascii=False)}

Ziele:
- Ein Treffen soll nur dann geplant werden, wenn das Gespräch deutlich romantisch, persönlich und konkret ist und das Interesse bereits sehr hoch ist.
- Das Interesse soll pro Runde nur langsam wachsen, maximal 10-15 Punkte.
- Wenn nur Smalltalk oder flache Konversation stattfindet, bleibt das Interesse stabil oder steigt nur leicht.
- Wenn der Spieler zu direkt ist oder nur Oberflächenverhalten zeigt, darf das Interesse nicht stark steigen.

Antworte nur mit JSON:
{{"meeting_planned": true/false, "interest_level": 0-100, "reason": "kurze Erklärung"}}
"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=180,
        )
        response_text = response.choices[0].message.content
        match = re.search(r"\{.*\}", response_text, re.S)
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
    except Exception:
        pass

    return {
        "meeting_planned": False,
        "interest_level": interest_level,
        "reason": "Deterministische Fallback-Analyse.",
    }


def format_chat_history_for_analysis(chat_history: List[Dict[str, str]]) -> str:
    """Format chat history as readable text"""
    formatted = []
    for msg in chat_history:
        role = "Spieler" if msg.get("role") == "user" else "Charakter"
        content = msg.get("content", "")
        formatted.append(f"{role}: {content}")
    return "\n".join(formatted)
