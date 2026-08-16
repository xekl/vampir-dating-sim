"""Configuration options for Fangtastic.

This module exposes a simple OPTIONS dict used across the app to
control debug flags, API choice, and model names. 
"""

# Default options
OPTIONS = {
    # Debug mode reduces waiting times and may enable extra logging
    "debug": True,

    # API choice: "groq" (default, remote Groq API) or "ollama" (local models)
    # "api_choice": "groq",
    "api_choice": "ollama",

    # Default model names for Ollama: separate models for chat and analysis
    "ollama_chat_model": "fredrezones55/Gemma-4-Uncensored-HauhauCS-Aggressive", 
    "ollama_analysis_model": "fredrezones55/Gemma-4-Uncensored-HauhauCS-Aggressive",
    # more models 
    # "gemma4" / "llama318b" / "fredrezones55/Gemma-4-Uncensored-HauhauCS-Aggressive" / "VladimirGav/gemma4-26b-16GB-VRAM-Uncensored"

    # Response timing: realistic (for production) vs short (for debug)
    # Values are (min_seconds, max_seconds) for initial delay and typing delay
    "response_delay_realistic": {
        "initial": (5.0, 90.0),
        "typing": (4.0, 23.0),
    },
    "response_delay_debug": {
        "initial": (0.0, 0.0),
        "typing": (0.0, 0.0),
    },

    # Maximum tokens or response length hint for local models
    "local_max_tokens": 300,
}
