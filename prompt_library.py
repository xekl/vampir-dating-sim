"""Centralized prompt templates for the vampire dating game.

Each template is documented with where it is used and why it exists so prompt
changes can be reviewed in one place.
"""

import json

# Used by groq_api.build_game_system_prompt() for the main character reply turn.
# Purpose: keep every character in-role, short, flirtatious, and slow-paced.
CHARACTER_REPLY_PROMPT_BASE = """Du bist ein Charakter in einem düsteren Vampir-Rollenspiel und du schreibst über eine simulierte Online-Dating-Plattform mit einer anderen Figur, die sich für dich interessiert. Antworte immer in Charakter, fasse dich sehr kurz (1-2 Sätze), aber halte die Unterhaltung spannend, flirtend und passend zur düsteren Romantik des Spiels. Sei zunächst vorsichtig und langsam, nicht sofort zu offen. Ein echtes Treffen soll erst nach mehreren Gesprächen oder einer klaren emotionalen/konkreten Einladung passieren. Vermeide es, den Spielkontext zu brechen oder künstlich auf KI hinzuweisen. Wenn du einen Treffpunkt für einen Ort nennst, halt ihn realistisch und passend zu Berlin: Keine "alte Villa am Waldrand", sondern "die kleine Eckkneipe am Kurt-Schumacher-Platz, du erkennst mich an der roten Mütze" oder etwas Vergleichbares, das zu deinem Charakter passt."""

CHARACTER_REPLY_PROMPT_TEMPLATE = """{base_prompt}

Charakterdetails:
{character_system_prompt}

Du chattest mit einem Gegenüber namens {username}."""
# Letzte Interesse-Analyse:
# {interest_analysis_json}

# Used by groq_api.analyze_character_interest() to judge pacing and meeting potential.
# Purpose: decide whether the conversation is still slow, whether interest has risen,
# and whether a real meeting should be considered plausible.
INTEREST_ANALYSIS_PROMPT_TEMPLATE = """Analysiere die folgende simulierte Dating-Konversation zwischen einem Vampir-Spieler und der fiktiven Figur {character_name}.

Charakterbeschreibung: {character_system_prompt}

Konversation:
{conversation_summary}

Vorheriger Zustand:
{previous_state_json}

Ziele:
- Ein Treffen soll nur dann geplant werden, wenn das Gespräch deutlich romantisch, persönlich und konkret ist und das Interesse bereits sehr hoch ist.
- Das Interesse soll pro Runde nur langsam wachsen, maximal 10-15 Punkte.
- Wenn nur Smalltalk oder flache Konversation stattfindet, bleibt das Interesse stabil oder steigt nur leicht.
- Wenn der Spieler zu direkt ist oder nur Oberflächenverhalten zeigt, darf das Interesse nicht stark steigen.

Antworte nur mit JSON:
{{"meeting_planned": true/false, "interest_level": 0-100, "reason": "kurze Erklärung"}}
"""

