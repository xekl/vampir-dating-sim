"""OpenRouter adapter implementing the shared chat and dialog-management API."""

import os
from typing import Any, Dict, List

import requests
import streamlit as st


OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"

# OpenRouter model names, selected from https://openrouter.ai/models
# "openrouter_chat_model": "openai/gpt-4o-mini",
# "openrouter_analysis_model": "openai/gpt-4o-mini",
# nvidia/nemotron-3-ultra-550b-a55b:free
# nvidia/nemotron-3.5-lightning:free
# nvidia/nemotron-3-super-120b-a12b:free
# thinkingmachines/inkling:free 
# apodex/apodex-1.1-mini:free
# cohere/north-mini-code:free

# TODO experiment with models, smarter handling
open_router_analysis_model = "nvidia/nemotron-3-ultra-550b-a55b:free"
open_router_chat_model = "nvidia/nemotron-3-ultra-550b-a55b:free"

def get_analysis_model() -> str:
    return open_router_analysis_model

def get_chat_model() -> str:
    return open_router_chat_model

def _get_api_key() -> str:
    api_key = st.secrets.get("OPEN_ROUTER_API_KEY", os.getenv("OPEN_ROUTER_API_KEY", ""))
    return api_key

def create_chat_completion(model: str, messages: List[Dict[str, str]], max_tokens: int | None = None, temperature: float | None = None, mode: str | None = None) -> str:

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
    }

    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    response = requests.post(
        OPENROUTER_CHAT_COMPLETIONS_URL,
        headers={
            "Authorization": f"Bearer {_get_api_key()}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    if response.json().get("error"):
        #TODO log error to error gist
        print("error while creating openrouter chat response:", response.json())
        #TODO actually handle the error ... 
        # e.g., a response could look like {'id': 'gen-1792082064-AIs3LL0F8ee5g2ALoiK6', 'error': {'message': 'Upstream error from Nvidia: Service temporarily overloaded', 'code': 503, 'metadata': {'error_type': 'provider_overloaded'}}}
        # then we need to switch to another model and recall
        return ""

    # get responste text 
    try: 
        response_json = response.json()
        response_text = response_json["choices"][0]["message"].get("content", "") or ""
    except Exception as error:
        #TODO log error to error gist
        print("Error parsing Openrouter text generation response as JSON:", str(error))
        print("response_json =", response_json)
        return response
    
    return response_text

