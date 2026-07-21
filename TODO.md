
overarching instructions for all characters
- always keep chat tone (no "Regienanweisungen")
- live-Uhrzeit mitgeben und für Treffen verwenden

- chars should be open about their kink almost from the start 

- one of them should want to DRINK blood instead?

- implement an automatic groq API key switcher that recognizes when the token limit is reached (model response starts with "...") and then overwrites the client with another one; assume that secrets.toml contains entries like GROQ_API_KEY_1, GROQ_API_KEY_2, GROQ_API_KEY_3 and load the keys as a list on startup of groq_api for easy client overwriting when necessary 
    Fehler bei der Verbindung: Error code: 429 - {'error': {'message': 'Rate limit reached for model `llama-3.3-70b-versatile` in organization 

- insert translation step? maybe dialog/progression gets better when prompting and responds happen in English and are just translated to German before writing to the chat