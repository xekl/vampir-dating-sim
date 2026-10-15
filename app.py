
import base64
import random
import time
from html import escape
from pathlib import Path

import streamlit as st

from app_options import OPTIONS
from data_loader_characters import load_all_characters, resolve_profile_image_path
from llm_api import chat_with_character, manage_dialog
from data_storer_gist_logger import log_chat_to_gist
from data_loader_users import load_all_users, get_user_by_username

# Configure page
st.set_page_config(
    page_title="Fangtastic - Dating For The Dark",
    page_icon="🧛",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark romantic theme
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

    .lose-message {
    background: linear-gradient(135deg, #ff3b30, #b00020);
    color: #fff;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    font-weight: bold;
    font-size: 1.1em;
    margin: 20px 0;
    box-shadow: 0 0 20px rgba(255, 59, 48, 0.45);
    }
</style>
""", unsafe_allow_html=True)

# Load user and character data from the filesystem.
USER_OPTIONS = get_user_by_username(load_all_users())

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.current_page = "login"
    st.session_state.current_character = None

if "all_characters" not in st.session_state:
    st.session_state.all_characters = load_all_characters()

def get_current_user_profile() -> dict:
    """Return the logged-in user's profile loaded from its user JSON."""
    #TODO make sure this also reflects and stores manual changes made on the profile page
    username = st.session_state.get("username") or ""
    user = USER_OPTIONS.get(username, {})
    return user.setdefault("profile", {
        "nickname": username,
        "age": 18,
        "gender": "",
        "interests": [],
        "looking_for": [],
        "bio": "",
    })

def configure_user_characters(username: str) -> None:
    """Initialize only the characters associated with the logged-in user."""
    user = USER_OPTIONS.get(username, {})
    character_ids = set(user.get("character_ids", []))
    #TODO all character-related states should go into here
    st.session_state.characters = {}
    st.session_state.profile_index = 0 # start with 0th character in char view

    # collect all characters for this user
    for char in st.session_state.all_characters:
        if char.get("id") in character_ids:
            st.session_state.characters[char["id"]] = char


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


def render_character_card_html(character: dict, won: bool, lost: bool) -> str:
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
    looking_for = escape(", ".join(character.get("looking_for", [])))

    if won:
        body_html = '<div class="win-message">✓ TREFFEN GEPLANT!</div>'
    elif lost:
        body_html = f'<div class="lose-message">🚫 {escape(character.get("name", ""))} hat dich blockiert.</div>'
    else:
        body_html = "" # we do not ever show interest to the user, it is an internal/debugging metric for the game logic only

    return f"""
    <div class="character-card">
        {image_html}
        <div class="character-name">{name}</div>
        <div class="character-info">
            {age} Jahre | {gender}<br>
            {bio}<br>
            Interessen: {interests}<br>
            Ich suche: {looking_for}
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
            login_option = USER_OPTIONS.get(username)
            # also allow for different cases
            if not login_option:
                login_option = USER_OPTIONS.get(username.lower())
            if not login_option:
                login_option = USER_OPTIONS.get(username.upper())
            if login_option and password == login_option["password"]:
                st.session_state.logged_in = True
                st.session_state.username = username
                configure_user_characters(username)
                st.session_state.current_page = "profiles"
                st.rerun()
            else:
                st.error("Ungültige Anmeldedaten.")
        
        st.markdown("---")
        st.markdown('<div style="text-align: center; color: #666; font-size: 0.8em; margin: 40px 0;">Eine Nacht voller Möglichkeiten erwartet dich...</div>', unsafe_allow_html=True)

def profiles_page():
    """Render profile overview with swiping"""
    # TODO actually add swiping??
    st.markdown(f'<div class="header">🧛 FANGTASTIC 🧛</div>', unsafe_allow_html=True)

    discover_tab, own_profile_tab = st.tabs(["Entdecken", "Mein Profil"])
    with own_profile_tab:
        user_profile_page()

    with discover_tab:
        st.markdown("---")
        st.markdown('<div style="text-align: center; color: #b0b0b0;">Diese Wesen interessieren sich für dich ...</div>', unsafe_allow_html=True)
        st.markdown("---")

        if "profile_index" not in st.session_state:
            st.session_state.profile_index = 0

        characters_list = list(st.session_state.characters.values())
        if not characters_list:
            st.error("Keine Wesen gefunden")
            return

        #TODO check if should be character here already not current_char
        current_char = characters_list[st.session_state.profile_index]
        won = current_char.get("meeting_planned")
        lost = current_char.get("user_blocked")
        st.markdown(
            render_character_card_html(current_char, won, lost),
            unsafe_allow_html=True,
        )

        # Profile navigation buttons
        col1, col2, col3 = st.columns(3)

        # TODO is there a way to prevent the whole page from jumping to the top 
        # on the rerun() when pressing the left/right buttons? 
        # Maybe with a session_state variable to remember the scroll position?
        # TODO is there a way to add swiping gestures for mobile users? 
        # Streamlit doesn't seem to have built-in support for that ...

        with col1:
            if st.button("< = = =", use_container_width=True):
                st.session_state.profile_index = (st.session_state.profile_index - 1) % len(characters_list)
                st.rerun()
        with col2:
            if st.button("CHATTEN", use_container_width=True):
                st.session_state.current_character = current_char["id"]
                st.session_state.current_page = "chat"
                st.rerun()
            # TODO style the CHATTTEN button (ONLY the chat button) to distinguish it from the left/right buttons
            # e.g., a pink outline or a glowing effect, to make it more inviting to click
        with col3:
            if st.button("= = = >", use_container_width=True):
                st.session_state.profile_index = (st.session_state.profile_index + 1) % len(characters_list)
                st.rerun()


def user_profile_page():
    """Render and save the logged-in user's dating profile."""
    profile = get_current_user_profile()
    st.subheader("Mein Profil")
    st.caption("So sehen dich andere auf Fangtastic.")

    with st.form("user_profile_form"):
        nickname = st.text_input("Spitzname", value=profile.get("nickname", ""), disabled=True)
        age = st.number_input("Alter", value=int(profile.get("age", 18)), step=1)
        gender = st.text_input("Geschlecht", value=profile.get("gender", ""))
        interests = st.text_input("Interessen", value=", ".join(profile.get("interests", [])))
        looking_for = st.text_input("Ich suche", value=", ".join(profile.get("looking_for", [])))
        bio = st.text_area("Bio", value=profile.get("bio", ""), height=120)

        if st.form_submit_button("Profil speichern", use_container_width=True):
            profile.update({
                "nickname": nickname.strip(),
                "age": age,
                "gender": gender.strip(),
                "interests": [item.strip() for item in interests.split(",") if item.strip()],
                "looking_for": [item.strip() for item in looking_for.split(",") if item.strip()],
                "bio": bio.strip(),
            })
            st.success("Dein Profil wurde gespeichert.")
            # TODO actually do that and store profile changes to
            # 1) use in the prompts for the characters, and
            # 2) allow saving/exporting for future sessions

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
    col1, debug_col, col3 = st.columns(3)
    with col1:
        if st.button("⬅️ Zurück", use_container_width=True):
            # Log the chat before leaving
            chat_history = character.get("messages", [])
            interest = character.get("interest_level", -1)
            won = character.get("meeting_planned", False)
            lost = character.get("blocked_user", False)

            if chat_history:
                #TODO maybe log with every message instead
                log_chat_to_gist(
                    character["name"],
                    character["id"],
                    st.session_state.username,
                    chat_history,
                    interest,
                    won,
                    lost,
                    "Chat beendet, zurück zum Profil"
                )
            
            st.session_state.current_page = "profiles"
            st.rerun()
    
    # debug info (visible only in debug mode)
    with debug_col:
        if OPTIONS.get("debug"):
            st.markdown(f"interest lvl: {character.get("interest_level")}")

    # state info 
    with col3:
        won = character.get("meeting_planned", False)    
        lost = character.get("blocked_user", False)    
        if won:
            st.button("✓ TREFFEN GEPLANT!", disabled=True, use_container_width=True)
        if lost:
            st.button("🚫 Geblockt", disabled=True, use_container_width=True)
    
    st.markdown("---")
    
    # Character info
    st.markdown(f"""
    <div style="background: rgba(255, 20, 147, 0.1); padding: 10px; border-radius: 5px; text-align: center; color: #b0b0b0; font-size: 0.9em;">
        {character.get("bio", "")}<br>
        Interessen: {", ".join(character.get("interests", []))}<br>
        Ich suche: {", ".join(character.get("looking_for", []))}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Chat history
    chat_history = character.get("messages", [])
    
    if not chat_history:
        st.markdown('<div style="text-align: center; color: #666;">Beginne ein Gespräch...</div>', unsafe_allow_html=True)
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
    
    # st.markdown("---")
    
    # Input area
    user_input = st.chat_input("Deine Nachricht:", key=f"chat_{character['id']}", disabled=lost)

    if user_input and not lost:

        print("sent input:" + user_input)
        print()

        # Write message 
        st.markdown(f'''
        <div class="chat-message chat-user">
            <strong>👤 Du:</strong> {user_input}
        </div>
        ''', unsafe_allow_html=True)

        # Add user message
        character.get("messages", []).append({
            "role": "user",
            "content": user_input
        })

        # Manage dialog
        management_result = manage_dialog(
            character.get("name", ""),
            character.get("character_strategy", ""),
            character.get("interest_level", 0),
            character.get("meeting_planned", False),
            character.get("user_blocked", False),
            character.get("messages", []),
            get_current_user_profile(),
        )
        character["interest_level"] = management_result.get("interest_level")
        character["user_blocked"] = management_result.get("user_blocked")
        character["meeting_planned"] = management_result.get("meeting_planned")
        next_turn_instructions = management_result.get("char_instructions")
        #TODO log current character state to character gist?

        # Get character response with a delay that depends on debug mode.
        # In debug mode delays are very short; otherwise use realistic pauses.
        delay_cfg = OPTIONS["response_delay_debug"] if OPTIONS.get("debug") else OPTIONS["response_delay_realistic"]
        time.sleep(random.uniform(*delay_cfg["initial"]))
        if OPTIONS.get("current_time_override"): 
            current_time = OPTIONS.get("current_time_override")
        else:
            current_time = time.strftime("%a, %d %b %Y, %H:%M")
        with st.spinner("tippt ..."):
            time.sleep(random.uniform(*delay_cfg["typing"]))
            response = chat_with_character(
                character.get("character_description", ""),
                current_time=current_time,
                username=st.session_state.username,
                chat_history=character.get("messages")[:-1],  # Exclude latest user message for context #TODO revise this, maybe keep message instead
                interest_level=character.get("interest_level"),
                user_blocked=character.get("user_blocked"),
                meeting_planned=character.get("meeting_planned"),
                next_turn_instructions=next_turn_instructions,
                user_message=user_input, #TODO because why is it added here again duh
                user_profile=get_current_user_profile(), #TODO this contains the name from above
            )
        
        # Add character response
        character["messages"].append({
            "role": "assistant",
            "content": response
        })

        # Send lose message if blocked
        if character.get("user_blocked"):
            character["messages"].append({
                "role": "assistant",
                "content": f"{character['name']} hat dich blockiert."
            })

        # and rerun 
        st.rerun()


# Main app routing
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.current_page == "profiles":
        profiles_page()
    elif st.session_state.current_page == "chat":
        chat_page()
