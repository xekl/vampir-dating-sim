# 🧛 FANGTASTIC - Vampire Dating Sim

Prototype for a LARP game. Meant to run on Streamlit Cloud with Groq, OpenRouter, or local Ollama models for in-game "hunting".

## OpenRouter

To use OpenRouter, set `OPENROUTER_API_KEY` in the environment or in `.streamlit/secrets.toml`, then set `OPTIONS["api_choice"]` to `"open_router"` in `fangtastic_options.py`. The default chat and analysis models are `openai/gpt-4o-mini`; change `openrouter_chat_model` and `openrouter_analysis_model` there to choose other models available on OpenRouter.
