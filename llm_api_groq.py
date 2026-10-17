
import json
import os
import re
from typing import Any, Dict, List

import streamlit as st
from groq import Groq

import llm_prompt_library


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

def get_chat_model():

    global chat_model_index

    groq_chat_models = [
        # see https://console.groq.com/docs/rate-limits
        # "llama-3.3-70b-versatile", # smartest chatter so far, depreciated -_-
        # "openai/gpt-oss-120b", # refuses to arrange meetings
        # "openai/gpt-oss-20b",
        # "openai/gpt-oss-safeguard-20b", 
        "qwen/qwen3.8-27b",
        # "groq/compound", # not great at following instructions, depreciated -_-
    ]
    chat_model_index = (chat_model_index + 1) % len(groq_chat_models)
    return groq_chat_models[chat_model_index]

def get_analysis_model():

    global analysis_model_index

    groq_analysis_models = [
        # "llama-3.3-70b-versatile", # also smartest reasoner, depreciated -_-
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b", 
        # "openai/gpt-oss-safeguard-20b", 
        "qwen/qwen3.8-27b",
        # "groq/compound", # not great at following instructions, depreciated -_-
    ]

    analysis_model_index = (analysis_model_index + 1) % len(groq_analysis_models)
    return groq_analysis_models[analysis_model_index]


groq_client = get_next_groq_client()


def create_chat_completion(model: str, messages: List[Dict[str, str]], max_tokens: int | None = None, temperature: float | None = None, mode: str | None = None) -> str:

    global groq_client
    global last_api_key_reached

    # Call groq API
    try: 
        if "gpt-oss" in model:
            response = groq_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={"reasoning_effort": "low"}
            )
        elif "qwen" in model:
            response = groq_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={"reasoning_effort": "none"}
            ) 
        else:
            response = groq_client.chat.completions.create(
                model=model,
                messages=messages,
                # temperature=0.2,
                max_tokens=max_tokens,
            )

    except Exception as error:
        #TODO log error to error gist
        print("error while creating groq chat response:", error)
        print("response:", response)
        rate_limit_error_model = str(error).split("Rate limit reached for model `")[1].split("`")[0] if "Rate limit reached for model" in str(error) else None
        if rate_limit_error_model:

            # Switch to the next API key and retry with a new client 
            print("rate limit reached for model, switching to API key", api_key_index+1)
            groq_client = get_next_groq_client()

            # But if you are just recursing through the keys now, also switch model 
            next_model = model 
            if last_api_key_reached > 3: 
                if mode == "chat":
                    next_model = get_chat_model()
                else:
                    next_model = get_analysis_model()
                last_api_key_reached = 0 # and reset key recursion check

            return create_chat_completion(next_model, messages, max_tokens, temperature, mode)

        return ""

    # get response text 
    try: 
        response_text = response.choices[0].message.content
    except Exception as error:
        #TODO log error to error gist
        print("Error parsing Openrouter text generation response as JSON:", str(error))
        print("response =", response)
        return response
    
    return response_text
