

- think about reducing token costs ...
- dialog manager does not manage anything 
prompts müssen viel kürzer werden!

-> alle Charakterprompts an Anja anpassen 
-> Konversation cutten, sobald zu lang
Fehler bei der Verbindung: Error code: 413 - {'error': {'message': 'Request Entity Too Large', 'type': 'invalid_request_error', 'code': 'request_too_large'}} 

UND DANN UPLOADEN 


- add refusal catcher for 
"Ich kann nicht auf Anfragen antworten, die Inhalte betreffen, die Minderjährige darstellen oder für diese geeignet sind."
Is the above chat reply a refusal to answer, e.g. because of a content filter? If it is a refusal, say exactly and only: REFUSAL
...

- add "fail state" - you suck, character blocked you 



- chars should be open about their kink almost from the start 
BUT NOT THAT OPEN AND THAT EARLY MICHI


- implement an automatic groq API key switcher that recognizes when the token limit is reached (see two instances of # Catch Rate Limit error for workarounds in groq_api module) and then either switches model, or overwrites the client with another one; assume that secrets.toml contains entries like GROQ_API_KEY_1, GROQ_API_KEY_2, GROQ_API_KEY_3 and load the keys as a list on startup of groq_api for easy client overwriting when necessary 
    Fehler bei der Verbindung: Error code: 429 - {'error': {'message': 'Rate limit reached for model `llama-3.3-70b-versatile` in organization 

- insert translation step? maybe dialog/progression gets better when prompting and responds happen in English and are just translated to German before writing to the chat