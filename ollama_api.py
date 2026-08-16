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

	model = OPTIONS.get("ollama_analysis_model", "gemma4")
	max_tokens = OPTIONS.get("local_max_tokens", 300)

	try:
		
		print("Managing dialog with ollama model:", model)
		print()

		payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens, "stream": False, "keep_alive": "10m"}
		response = requests.post("http://localhost:11434/api/generate", json=payload)
		response.raise_for_status()

		try:
			response_json = response.json()
			response_text = response_json["response"].strip()

		except ValueError as e:
			print("Error parsing Ollama text generation response as JSON:", e)
			return response.text.strip()
		
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

	model = OPTIONS.get("ollama_chat_model", "gemma4")
	max_tokens = OPTIONS.get("local_max_tokens", 300)
	
	print("entering chat_with_character with ollama model:", model)

	# Build system prompt
	char_system_prompt = prompt_library.CHARACTER_REPLY_PROMPT.format(
		current_time=current_time,
		character_description=character_description,
		username=username,
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
	
    # Call the Ollama chat endpoint
	try:
		payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "stream": False, "think": False, "keep_alive": "10m"}
		response = requests.post("http://localhost:11434/api/chat", json=payload)
		response.raise_for_status()
		try:
			response_json = response.json()

			print("Ollama chat response JSON:", response_json)
			print()

			character_answer = response_json.get("message").get("content", "").strip()
			return character_answer
		except ValueError as e:
			print("Error parsing Ollama chat response as JSON:", e)
			return response.text.strip()
	
	except Exception as e:
		return f"Fehler bei der Verbindung (ollama chat): {str(e)}"
		