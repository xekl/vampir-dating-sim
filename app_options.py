"""Configuration options for Fangtastic.

This module exposes a simple OPTIONS dict used across the app to
control debug flags, API choice, and model names. 
"""

# Default options
OPTIONS = {

    # Debug mode reduces waiting times and may enable extra logging
    "debug": False,

    # Overwrite current time with this time if necessary
    # "current_time_override": None,  # e.g. "2024-06-01 20:00"
    # "current_time_override": "Samstag, 15. August, 23:00",

    # API choice: "groq", "open_router" (remote APIs), or "ollama" (local models)
    "api_choice": "groq",
    # "api_choice": "open_router",
    # "api_choice": "ollama",

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
