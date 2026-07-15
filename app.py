import random
import time
import streamlit as st
import json
from character_loader import load_all_characters, get_character_by_id, resolve_profile_image_path
from groq_api import chat_with_character, analyze_character_interest
from gist_logger import log_chat_to_gist

# Configure page
st.set_page_config(
    page_title="Fangtastic - Vampire Dating",
    page_icon="🧛",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark vampire theme
st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
    }
    
    body {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a0015 100%);
        color: #e0e0e0;
        font-family: 'Courier New', monospace;
    }
    
    .main {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a0015 100%);
    }
    
    .stContainer {
        max-width: 600px;
    }
    
    .header {
        text-align: center;
        color: #ff1493;
        font-size: 2.5em;
        font-weight: bold;
        text-shadow: 0 0 20px #ff1493;
        margin: 20px 0;
    }
    
    .character-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 2px solid #ff1493;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 0 20px rgba(255, 20, 147, 0.3);
        text-align: center;
    }
    
    .character-image {
        width: 100%;
        max-width: 300px;
        height: 300px;
        border: 3px solid #ff1493;
        border-radius: 10px;
        margin: 10px auto;
        object-fit: cover;
        box-shadow: 0 0 15px rgba(255, 20, 147, 0.5);
    }
    
    .character-name {
        font-size: 1.8em;
        color: #ff1493;
        margin: 15px 0 5px 0;
        text-shadow: 0 0 10px #ff1493;
    }
    
    .character-info {
        color: #b0b0b0;
        font-size: 0.95em;
        margin: 5px 0;
    }
    
    .interest-meter {
        width: 100%;
        height: 30px;
        background: #0a0a0a;
        border: 2px solid #ff1493;
        border-radius: 15px;
        margin: 15px 0;
        position: relative;
        overflow: hidden;
    }
    
    .interest-fill {
        height: 100%;
        background: linear-gradient(90deg, #ff1493, #ff69b4);
        border-radius: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #000;
        font-weight: bold;
        font-size: 0.8em;
    }
    
    .chat-message {
        margin: 15px 0;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #ff1493;
    }
    
    .chat-user {
        background: rgba(255, 20, 147, 0.1);
        text-align: right;
        border-left: none;
        border-right: 4px solid #ff1493;
    }
    
    .chat-character {
        background: rgba(20, 147, 255, 0.1);
        border-left: 4px solid #00bfff;
    }
    
    .button-won {
        background: linear-gradient(135deg, #00ff00, #00cc00) !important;
        color: #000 !important;
        font-weight: bold !important;
        box-shadow: 0 0 20px rgba(0, 255, 0, 0.6) !important;
    }
    
    .button-normal {
        background: linear-gradient(135deg, #ff1493, #ff69b4) !important;
        color: #fff !important;
    }
    
    .win-message {
        background: linear-gradient(135deg, #00ff00, #00cc00);
        color: #000;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 1.2em;
        margin: 20px 0;
        box-shadow: 0 0 30px rgba(0, 255, 0, 0.6);
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    .control-buttons {
        display: flex;
        gap: 10px;
        justify-content: center;
        margin: 20px 0;
        flex-wrap: wrap;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.current_page = "login"
    st.session_state.current_character = None
    st.session_state.characters = {}
    st.session_state.character_chats = {}
    st.session_state.character_wins = {}
    st.session_state.character_interests = {}

# Load characters on startup
if not st.session_state.characters:
    characters = load_all_characters()
    for char in characters:
        st.session_state.characters[char["id"]] = char
        st.session_state.character_chats[char["id"]] = []
        st.session_state.character_wins[char["id"]] = False
        st.session_state.character_interests[char["id"]] = 0

def login_page():
    """Render login page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="header">🧛 FANGTASTIC 🧛</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; color: #b0b0b0; margin: 20px 0;">Dark Love Dating</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown('<div style="text-align: center; color: #ff1493; font-size: 0.9em; margin: 20px 0;">Finde deine perfekte Verbindung in der Nacht...</div>', unsafe_allow_html=True)
        
        username = st.text_input("Benutzername", placeholder="Gib deinen Namen ein")
        password = st.text_input("Passwort", type="password", placeholder="Dein Passwort")
        
        st.markdown("---")
        
        if st.button("🌙 EINLOGGEN", use_container_width=True):
            # Hardcoded credentials
            if username == "fanggirl" and password == "blut123":
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.current_page = "profiles"
                st.rerun()
            else:
                st.error("Ungültige Anmeldedaten.")
        
        st.markdown("---")
        st.markdown('<div style="text-align: center; color: #666; font-size: 0.8em; margin: 40px 0;">Eine Nacht voller Möglichkeiten erwartet dich...</div>', unsafe_allow_html=True)

def profiles_page():
    """Render profile overview with swiping"""
    st.markdown(f'<div class="header">🧛 FANGTASTIC 🧛</div>', unsafe_allow_html=True)
    
    # col1, col2 = st.columns([1, 1])
    # with col1:
    #     if st.button("🚪 Abmelden", use_container_width=True):
    #         st.session_state.logged_in = False
    #         st.session_state.username = None
    #         st.session_state.current_page = "login"
    #         st.rerun()
    # with col2:
    #     if st.button("📊 Stats", use_container_width=True):
    #         st.session_state.current_page = "stats"
    #         st.rerun()
    
    st.markdown("---")
    st.markdown('<div style="text-align: center; color: #b0b0b0;">Diese Wesen interessieren sich für dich ...</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Initialize character index if needed
    if "profile_index" not in st.session_state:
        st.session_state.profile_index = 0
    
    characters_list = list(st.session_state.characters.values())
    if not characters_list:
        st.error("Keine Charaktere gefunden!")
        return
    
    current_char = characters_list[st.session_state.profile_index]
    
    # Display character card
    st.markdown('<div class="character-card">', unsafe_allow_html=True)
    
    image_path = resolve_profile_image_path(current_char.get("profile_image"))
    if image_path:
        st.image(image_path, width=300)
    else:
        st.markdown(f"""
        <div style="width: 100%; height: 300px; background: linear-gradient(135deg, #ff1493, #8b0051); 
                    border-radius: 10px; display: flex; align-items: center; justify-content: center; 
                    color: #fff; font-size: 3em; font-weight: bold;">
            🧛
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f'<div class="character-name">{current_char["name"]}</div>', unsafe_allow_html=True)
    
    age = current_char.get("age", "?")
    gender = current_char.get("gender", "?")
    bio = current_char.get("bio", "")
    interests = ", ".join(current_char.get("interests", []))
    
    st.markdown(f"""
    <div class="character-info">
        👥 {age} Jahre | {gender}<br>
        💭 {bio}<br>
        ❤️ {interests}
    </div>
    """, unsafe_allow_html=True)
    
    # Interest meter
    interest = st.session_state.character_interests.get(current_char["id"], 0)
    won = st.session_state.character_wins.get(current_char["id"], False)
    
    if won:
        status = "✓ TREFFEN GEPLANT!"
        st.markdown(f"""
        <div class="win-message">✓ TREFFEN GEPLANT!</div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="interest-meter">
            <div class="interest-fill" style="width: {interest}%;">
                {interest}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True) # end of character card (?)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⬅️ Vorher", use_container_width=True):
            st.session_state.profile_index = (st.session_state.profile_index - 1) % len(characters_list)
            st.rerun()
    
    with col2:
        if st.button("💬 CHATTEN", use_container_width=True):
            st.session_state.current_character = current_char["id"]
            st.session_state.current_page = "chat"
            st.rerun()
    
    with col3:
        if st.button("Nächste ➡️", use_container_width=True):
            st.session_state.profile_index = (st.session_state.profile_index + 1) % len(characters_list)
            st.rerun()

def chat_page():
    """Render chat interface"""

    if not st.session_state.current_character:
        st.error("Kein Charakter ausgewählt!")
        return
    
    character = st.session_state.characters.get(st.session_state.current_character)
    if not character:
        st.error("Charakter nicht gefunden!")
        return
    
    st.markdown(f'<div class="header">{character["name"]}</div>', unsafe_allow_html=True)
    
    # Buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬅️ Zurück", use_container_width=True):
            # Log the chat before leaving
            chat_id = character["id"]
            chat_history = st.session_state.character_chats.get(chat_id, [])
            interest = st.session_state.character_interests.get(chat_id, 0)
            won = st.session_state.character_wins.get(chat_id, False)
            
            if chat_history:
                log_chat_to_gist(
                    character["name"],
                    chat_id,
                    st.session_state.username,
                    chat_history,
                    interest,
                    won,
                    "Chat beendet, zurück zum Profil"
                )
            
            st.session_state.current_page = "profiles"
            st.rerun()
    
    with col2:
        if st.button("🔄 Chat löschen", use_container_width=True):
            st.session_state.character_chats[character["id"]] = []
            st.rerun()
    
    with col3:
        interest = st.session_state.character_interests.get(character["id"], 0)
        won = st.session_state.character_wins.get(character["id"], False)
        
        if won:
            st.button("✓ TREFFEN GEPLANT!", disabled=True, use_container_width=True)
        else:
            st.write(f"📊 Interesse: {interest}%")
    
    st.markdown("---")
    
    # Character info
    st.markdown(f"""
    <div style="background: rgba(255, 20, 147, 0.1); padding: 10px; border-radius: 5px; text-align: center; color: #b0b0b0; font-size: 0.9em;">
        {character.get("bio", "")}<br>
        ❤️ {", ".join(character.get("interests", []))}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Chat history
    chat_history = st.session_state.character_chats.get(character["id"], [])
    
    if not chat_history:
        st.markdown('<div style="text-align: center; color: #666;">Starte ein Gespräch...</div>', unsafe_allow_html=True)
    else:
        for msg in chat_history:
            if msg["role"] == "user":
                st.markdown(f'''
                <div class="chat-message chat-user">
                    <strong>👤 Du:</strong> {msg["content"]}
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="chat-message chat-character">
                    <strong>🧛 {character["name"]}:</strong> {msg["content"]}
                </div>
                ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Input area
    # user_input = st.text_input("Deine Nachricht:", key=f"chat_{character['id']}")
    user_input = st.chat_input("Deine Nachricht:", key=f"chat_{character['id']}")
    
    if user_input:

        print("sent input:" + user_input)

        # Add user message
        st.session_state.character_chats[character["id"]].append({
            "role": "user",
            "content": user_input
        })
        
        # Get character response with a short, realistic typing delay.
        time.sleep(random.uniform(0.6, 1.4))
        with st.spinner("tippt..."):
            system_prompt = character.get("system_prompt", "")
            response = chat_with_character(
                system_prompt,
                st.session_state.character_chats[character["id"]][:-1],  # Exclude latest user message for context
                user_input
            )
        
        # Add character response
        st.session_state.character_chats[character["id"]].append({
            "role": "assistant",
            "content": response
        })
        
        # Analyze interest in the background and keep the UI focused on the chat.
        print("analyzing interest for character:", character["name"])
        analysis = analyze_character_interest(
            character["name"],
            system_prompt,
            character.get("win_condition_keywords", []),
            st.session_state.character_chats[character["id"]]
        )
        print("analysis result:", analysis)
        
        st.session_state.character_interests[character["id"]] = analysis.get("interest_level", 0)
        
        if analysis.get("interested", False):
            st.session_state.character_wins[character["id"]] = True
        
        user_input = ""

        st.rerun()

def stats_page():
    """Render statistics page"""
    st.markdown(f'<div class="header">📊 DEINE STATISTIKEN</div>', unsafe_allow_html=True)
    
    if st.button("⬅️ Zurück", use_container_width=True):
        st.session_state.current_page = "profiles"
        st.rerun()
    
    st.markdown("---")
    
    characters_list = list(st.session_state.characters.values())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        won_count = sum(1 for char_id in st.session_state.character_wins if st.session_state.character_wins[char_id])
        st.metric("Treffen geplant", won_count)
    with col2:
        total_chars = len(characters_list)
        st.metric("Charaktere", total_chars)
    with col3:
        avg_interest = int(sum(st.session_state.character_interests.values()) / len(characters_list)) if characters_list else 0
        st.metric("Ø Interesse", f"{avg_interest}%")
    
    st.markdown("---")
    st.markdown("### Charakter-Übersicht")
    
    for character in characters_list:
        char_id = character["id"]
        won = st.session_state.character_wins.get(char_id, False)
        interest = st.session_state.character_interests.get(char_id, 0)
        chat_count = len(st.session_state.character_chats.get(char_id, []))
        
        status = "✓ TREFFEN GEPLANT" if won else f"{interest}% interessiert"
        st.write(f"**{character['name']}** ({character['age']} Jahre) - {status} | {chat_count} Nachrichten")

# Main app routing
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.current_page == "profiles":
        profiles_page()
    elif st.session_state.current_page == "chat":
        chat_page()
    elif st.session_state.current_page == "stats":
        stats_page()
