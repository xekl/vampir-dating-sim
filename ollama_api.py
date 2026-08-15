"""Ollama HTTP adapter

This module posts prompts to a local Ollama HTTP endpoint and returns
the generated text. It provides `manage_dialog` and
`chat_with_character` with the same signatures as `groq_api` so the
rest of the app can call either backend interchangeably.
"""

import json
import re
from typing import Any, Dict, List

import requests
import prompt_library
from fangtastic_options import OPTIONS


def format_chat_history_for_analysis(chat_history: List[Dict[str, str]]) -> str:
	formatted = []
	message_cap = 7
	for msg in chat_history[-message_cap:]:
		role = "Spieler" if msg.get("role") == "user" else "Charakter"
		content = msg.get("content", "")
		formatted.append(f"{role}: {content}")
	return "\n".join(formatted)


def _post_generate(model: str, prompt: str, max_tokens: int = 300) -> str:
	
	url = OPTIONS.get("ollama_http_url", "http://localhost:11434/api/generate")
	
	payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens, "stream": False}
	response = requests.post(url, json=payload)
	response.raise_for_status()
	
	print("Ollama response:", response)
	print()
	
	try:
		response_json = response.json()
		if isinstance(response_json, dict) and "response" in response_json:
			return response_json["response"].strip()

	except ValueError:
		pass
	
	return response.text.strip()


def manage_dialog(
	character_name: str,
	character_strategy: str,
	previous_state: Dict[str, Any],
	chat_history: List[Dict[str, str]],
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

	conversation_summary = format_chat_history_for_analysis(chat_history)

	prompt = prompt_library.DIALOG_MANAGEMENT_PROMPT.format(
		character_name=character_name,
		conversation_summary=conversation_summary,
		character_strategy=character_strategy,
		previous_state_json=json.dumps(previous_state, ensure_ascii=False),
	)

	model = OPTIONS.get("local_model_name", "gemma4")
	max_tokens = OPTIONS.get("local_max_tokens", 300)

	try:
		
		print("Managing dialog with ollama model:", model)
		print()
		
		response_text = _post_generate(model, prompt, max_tokens=max_tokens)
		
		print("Dialog management response:", response_text)
		print()
		
		match = re.search(r"\{.*\}", response_text, re.S)
		if match:
			parsed = json.loads(match.group(0))
			interest_level = int(parsed.get("interest_level", previous_level))
			interest_level = min(100, max(0, interest_level))
			delta = interest_level - previous_level
			if abs(delta) > 15:
				interest_level = previous_level + max(-15, min(15, delta))
			meeting_planned = bool(parsed.get("meeting_planned", False))
			user_blocked = bool(parsed.get("user_blocked", False))
			char_instructions = str(parsed.get("char_instructions", ""))
			return {
				"meeting_planned": meeting_planned,
				"interest_level": interest_level,
				"user_blocked": user_blocked,
				"reason": str(parsed.get("reason", ""))[:160],
				"char_instructions": char_instructions,
			}

		return {
			"meeting_planned": previous_meeting,
			"interest_level": previous_level,
			"user_blocked": previous_blocked,
			"reason": "Kein JSON, nur: " + response_text[:200],
			"char_instructions": "",
		}

	except Exception as e:
		return {
			"meeting_planned": False,
			"interest_level": previous_level,
			"user_blocked": previous_blocked,
			"reason": f"Fehler: {str(e)[:140]}",
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

	model = OPTIONS.get("local_model_name", "gemma4")
	max_tokens = OPTIONS.get("local_max_tokens", 300)
	
	print("entering chat_with_character with ollama model:", model)

	char_system_prompt = prompt_library.CHARACTER_REPLY_PROMPT.format(
		current_time=current_time,
		character_description=character_description,
		username=username,
	)

	history = format_chat_history_for_analysis(chat_history)
	next_turn_instructions = management_result.get("char_instructions", "")

    # TODO 
	full_prompt = ( # WHY
		f"{char_system_prompt}\n\nVorherige Unterhaltung:\n{history}\n\n"
		f"Spieler: {user_message}\n\nSystem-Ergänzung: {next_turn_instructions}\n\n"
		"Antworte in der Rolle als reiner Dialog-Text."
	)

	try:
		character_response = _post_generate(model, full_prompt, max_tokens=max_tokens)
		
		print("chat response:", character_response)
		print()
		
		return character_response

	except Exception as e:
		return f"Fehler bei der Verbindung (ollama): {str(e)}"
