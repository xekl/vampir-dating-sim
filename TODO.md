
overarching instructions for all characters
- always keep chat tone (no "Regienanweisungen")
- live-Uhrzeit mitgeben und für Treffen verwenden

- Fälle von "I’m sorry, but I can’t continue this conversation." verhindern ...
-> Modell soll in dem Fall was schreiben wie 
"Dieser Inhalt wurde von Fangtastic geblockt. Bitte halten Sie die Konversation zivilisiert."

- chars should be open about their kink almost from the start 

- implement an automatic groq API key switcher that recognizes when the token limit is reached (see two instances of # Catch Rate Limit error for workarounds in groq_api module) and then either switches model, or overwrites the client with another one; assume that secrets.toml contains entries like GROQ_API_KEY_1, GROQ_API_KEY_2, GROQ_API_KEY_3 and load the keys as a list on startup of groq_api for easy client overwriting when necessary 
    Fehler bei der Verbindung: Error code: 429 - {'error': {'message': 'Rate limit reached for model `llama-3.3-70b-versatile` in organization 

- insert translation step? maybe dialog/progression gets better when prompting and responds happen in English and are just translated to German before writing to the chat