import base64
import random
import time
from html import escape
from pathlib import Path

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
            
    .st-key-chat-button .stButton button {
        box-shadow: 0 0 20px rgba(255, 20, 147, 0.3);
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
        char["interest_analysis"] = {"meeting_planned": False, "interest_level": 0, "reason": ""}
        st.session_state.characters[char["id"]] = char
        st.session_state.character_chats[char["id"]] = []
        st.session_state.character_wins[char["id"]] = False
        st.session_state.character_interests[char["id"]] = 0


def get_image_data_url(image_path: str | None) -> str | None:
    """Embed an image file as a data URL so it can be rendered inside one HTML block."""
    if not image_path:
        return None

    path = Path(image_path)
    if not path.exists():
        return None

    mime_type = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    with path.open("rb") as handle:
        encoded = base64.b64encode(handle.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


# def render_character_card_html(character: dict, interest: int, won: bool) -> str:
def render_character_card_html(character: dict, won: bool) -> str:
    """Render the whole card as a single HTML fragment so Streamlit keeps it wrapped."""
    image_path = resolve_profile_image_path(character.get("profile_image"))
    image_url = get_image_data_url(image_path)

    if image_url:
        image_html = f'<img src="{image_url}" class="character-image" />'
    else:
        image_html = f"""
        <div class="character-image" style="display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #ff1493, #8b0051); color: #fff; font-size: 3em; font-weight: bold;">
            🧛
        </div>
        """

    name = escape(character.get("name", ""))
    age = character.get("age", "?")
    gender = character.get("gender", "?")
    bio = escape(character.get("bio", ""))
    interests = escape(", ".join(character.get("interests", [])))

    if won:
        body_html = '<div class="win-message">✓ TREFFEN GEPLANT!</div>'
    else: 
        body_html = ''
    # else:
    #     body_html = f"""
    #     <div class="interest-meter">
    #         <div class="interest-fill" style="width: {interest}%;">{interest}%</div>
    #     </div>
    #     """

    return f"""
    <div class="character-card">
        {image_html}
        <div class="character-name">{name}</div>
        <div class="character-info">
            👥 {age} Jahre | {gender}<br>
            💭 {bio}<br>
            ❤️ {interests}
        </div>
        {body_html}
    </div>
    """


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
    # interest = st.session_state.character_interests.get(current_char["id"], 0)
    won = st.session_state.character_wins.get(current_char["id"], False)
    st.markdown(
        # render_character_card_html(current_char, interest, won),
        render_character_card_html(current_char, won),
        unsafe_allow_html=True,
    )

    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        # TODO is there a way to prevent the whole page from jumping to the top 
        # on the rerun() when pressing the left/right buttons? 
        # Maybe with a session_state variable to remember the scroll position?
        # TODO is there a way to add swiping gestures for mobile users? 
        # Streamlit doesn't have built-in support for that.
        if st.button(" ⏪ ⏪ ⏪ ", use_container_width=True):
            st.session_state.profile_index = (st.session_state.profile_index - 1) % len(characters_list)
            st.rerun()
    with col2:
        # TODO this button is not styled as expected, need to fix Streamlit button styling
        if st.button("CHATTEN", key="chat-button", use_container_width=True):
            st.session_state.current_character = current_char["id"]
            st.session_state.current_page = "chat"
            st.rerun()
    with col3:
        if st.button(" ⏩ ⏩ ⏩ ", use_container_width=True):
            st.session_state.profile_index = (st.session_state.profile_index + 1) % len(characters_list)
            st.rerun()

def chat_page():
    """Render chat interface"""

    if not st.session_state.current_character:
        st.error("Kontakt nicht gefunden")
        return
    
    character = st.session_state.characters.get(st.session_state.current_character)
    if not character:
        st.error("Kontakt nicht gefunden!")
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
        # if st.button("🔄 Chat löschen", use_container_width=True):
        #     st.session_state.character_chats[character["id"]] = []
        #     st.rerun()
        st.markdown("")
    
    with col3:
        interest = st.session_state.character_interests.get(character["id"], 0)
        won = st.session_state.character_wins.get(character["id"], False)
        
        if won:
            st.button("✓ TREFFEN GEPLANT!", disabled=True, use_container_width=True)
        # else:
        #     st.write(f"📊 Interesse: {interest}%")
    
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
                st.session_state.characters[character["id"]]["interest_analysis"],
                user_input
            )
        
        # Add character response
        st.session_state.character_chats[character["id"]].append({
            "role": "assistant",
            "content": response
        })
        
        # Analyze interest in the background and keep the UI focused on the chat.
        analysis = analyze_character_interest(
            character["name"],
            system_prompt,
            st.session_state.characters[character["id"]]["interest_analysis"],
            st.session_state.character_chats[character["id"]]
        )
        print("analysis result:", analysis)
        
        st.session_state.character_interests[character["id"]] = analysis.get("interest_level", 0)
        
        if analysis.get("meeting_planned", False): # set win state 
            st.session_state.character_wins[character["id"]] = True
        else: # if the character is not meeting, yet, save their interest analysis
            st.session_state.characters[character["id"]]["interest_analysis"] = analysis
        
        user_input = ""

        st.rerun()

# def stats_page():
#     """Render statistics page"""
#     st.markdown(f'<div class="header">📊 DEINE STATISTIKEN</div>', unsafe_allow_html=True)
    
#     if st.button("⬅️ Zurück", use_container_width=True):
#         st.session_state.current_page = "profiles"
#         st.rerun()
    
#     st.markdown("---")
    
#     characters_list = list(st.session_state.characters.values())
    
#     col1, col2, col3 = st.columns(3)
#     with col1:
#         won_count = sum(1 for char_id in st.session_state.character_wins if st.session_state.character_wins[char_id])
#         st.metric("Treffen geplant", won_count)
#     with col2:
#         total_chars = len(characters_list)
#         st.metric("Charaktere", total_chars)
#     with col3:
#         avg_interest = int(sum(st.session_state.character_interests.values()) / len(characters_list)) if characters_list else 0
#         st.metric("Ø Interesse", f"{avg_interest}%")
    
#     st.markdown("---")
#     st.markdown("### Charakter-Übersicht")
    
#     for character in characters_list:
#         char_id = character["id"]
#         won = st.session_state.character_wins.get(char_id, False)
#         interest = st.session_state.character_interests.get(char_id, 0)
#         chat_count = len(st.session_state.character_chats.get(char_id, []))
        
#         status = "✓ TREFFEN GEPLANT" if won else f"{interest}% interessiert"
#         st.write(f"**{character['name']}** ({character['age']} Jahre) - {status} | {chat_count} Nachrichten")

# Main app routing
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.current_page == "profiles":
        profiles_page()
    elif st.session_state.current_page == "chat":
        chat_page()
    # elif st.session_state.current_page == "stats":
    #     stats_page()
