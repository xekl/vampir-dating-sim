import streamlit as st
import requests
from datetime import datetime
from typing import Dict, List

# GitHub Gist Logging 
# to setup,
#  go to https://gist.github.com/
#  create a new Gist (private)
#  note Gist ID from URL
#  if necessary, go to https://github.com/settings/tokens
#  click "Generate new token" (only gist scope)
#  insert all relevant info (token, id, username) into secrets.toml

def log_chat_to_gist(
    character_name: str,
    character_id: str,
    player_name: str,
    chat_history: List[Dict[str, str]],
    interest_level: int,
    won: bool,
    reason: str = ""
) -> bool:
    """
    Log chat session to a GitHub Gist
    
    Args:
        character_name: Name of the character
        character_id: ID of the character
        player_name: Player's username (from login)
        chat_history: The chat history
        interest_level: Final interest level (0-100)
        won: Whether the player won this character
        reason: Optional reason/summary
    
    Returns:
        True if logging was successful, False otherwise
    """
    try:
        GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
        gist_id = st.secrets.get("gist_id", "")
        
        if not GITHUB_TOKEN or GITHUB_TOKEN.startswith("ghp_dummy"):
            print("GitHub Gist token not configured")
            return False
        
        if not gist_id or gist_id == "your_gist_id_here":
            print("GitHub Gist ID not configured")
            return False
        
        # Format the log entry
        timestamp = datetime.now().isoformat()
        status = "WON ✓" if won else "INCOMPLETE"
        
        log_entry = f"""
### [{timestamp}] {character_name} - {status} (Interest: {interest_level}%)

**Spieler:** {player_name}
**Charakter:** {character_name} ({character_id})
**Status:** {status}
**Interessenslevel:** {interest_level}%
{f'**Grund:** {reason}' if reason else ''}

**Konversation:**
"""
        
        # Add conversation
        for msg in chat_history:
            role = "👤 Spieler" if msg.get("role") == "user" else "🧛 Charakter"
            content = msg.get("content", "")
            log_entry += f"\n{role}: {content}"
        
        log_entry += "\n\n---\n\n"
        
        # Get current gist content
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        gist_url = f"https://api.github.com/gists/{gist_id}"
        
        response = requests.get(gist_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch gist: {response.status_code}")
            return False
        
        gist_data = response.json()
        
        # Get the main file name
        files = gist_data.get("files", {})
        main_file = None
        for filename in files:
            main_file = filename
            break
        
        if not main_file:
            main_file = "vampire_larp_logs.md"
        
        # Append to existing content
        existing_content = files.get(main_file, {}).get("content", "")
        new_content = existing_content + log_entry
        
        # Update gist
        update_data = {
            "files": {
                main_file: {
                    "content": new_content
                }
            }
        }
        
        response = requests.patch(gist_url, headers=headers, json=update_data)
        
        if response.status_code == 200:
            print(f"Successfully logged to gist: {character_name}")
            return True
        else:
            print(f"Failed to update gist: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"Error logging to gist: {str(e)}")
        return False
