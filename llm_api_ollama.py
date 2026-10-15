"""Ollama HTTP adapter

This module posts prompts to a local Ollama HTTP endpoint and returns
the generated text. It provides `manage_dialog` and
`chat_with_character` with the same signatures as `groq_api` so the
rest of the app can call either backend interchangeably.
"""

from typing import Any, Dict, List

import requests
from app_options import OPTIONS


OLLAMA_CHAT_COMPLETIONS_URL = "http://localhost:11434/api/chat"

# Default model names for Ollama: separate models for chat and analysis
# ollama_chat_model = "fredrezones55/Gemma-4-Uncensored-HauhauCS-Aggressive"
# ollama_analysis_model = "fredrezones55/Gemma-4-Uncensored-HauhauCS-Aggressive"
ollama_chat_model = "gemma4"
ollama_analysis_model = "gemma4"
# more models 
# "gemma4" / "llama318b" / "fredrezones55/Gemma-4-Uncensored-HauhauCS-Aggressive" / "VladimirGav/gemma4-26b-16GB-VRAM-Uncensored"


def get_analysis_model() -> str:
    return ollama_analysis_model

def get_chat_model() -> str:
    return ollama_chat_model

def create_chat_completion(model: str, messages: List[Dict[str, str]], max_tokens: int | None = None, temperature: float | None = None, mode: str | None = None) -> str:

	payload: Dict[str, Any] = {
		"model": model,
		"messages": messages,
		"max_tokens": OPTIONS.get("local_max_tokens", 300),
		"stream": False, 
		"keep_alive": "10m",
	}

	if temperature is not None:
		payload["temperature"] = temperature
	if max_tokens is not None:
		payload["max_tokens"] = max_tokens

	response = requests.post(OLLAMA_CHAT_COMPLETIONS_URL, json=payload)
	response.raise_for_status()

	try:
		response_json = response.json()
		response_text = response_json.get("message").get("content")

	except Exception as error:
		#TODO log error to error gist
		print("Error parsing Ollama text generation response as JSON:", str(error))
		print("response_json =", response_json)
		return response

	return response_text