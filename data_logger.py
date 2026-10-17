import streamlit as st
import requests
from datetime import datetime
from typing import Dict, List

GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GIST_ID = st.secrets.get("GIST_ID", "")

ERROR_TARGET_FILE = "fangtastic_logs.md"
LOG_TARGET_FILE = "fangtastic_logs.md"

# GitHub Gist Logging 
# to setup,
#  go to https://gist.github.com/
#  create a new Gist (private)
#  note Gist ID from URL
#  if necessary, go to https://github.com/settings/tokens
#  click "Generate new token" (only gist scope)
#  insert all relevant info (token, id, username) into secrets.toml


def log_to_gist(target_file: str, log_entry: str, mode: str = "append") -> requests.Response:

    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    gist_url = f"https://api.github.com/gists/{GIST_ID}"

    # retrieve existing gist content
    response = requests.get(gist_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch gist: {response.status_code}")
    gist_data = response.json()

    print("gist_data:", gist_data)

    files = gist_data.get("files", {})

    update_data = {}
    if mode == "append": # log mode append (default)

        # if the target file already exists, retrieve its content
        existing_content = ""
        if target_file in files: 
            existing_content = files.get(target_file, {}).get("content", "")

        # append new content to existing content
        new_content = existing_content + log_entry
        update_data = {
                "files": {
                    target_file: {
                        "content": new_content
                    }
                }
            }

    else: # log mode replace (overwrite with any other string)
        update_data = {
                "files": {
                    target_file: {
                        "content": log_entry
                    }
                }
            }
    
    # update gist
    response = requests.patch(gist_url, headers=headers, json=update_data)
    return response


def log_error(username: str, position: str, error_message: str) -> None:
    log_line = "------- " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " - ERROR - " + username + " - " + position + " -------"
    log_line += "\n  "+ error_message + "\n\n"
    response = log_to_gist(ERROR_TARGET_FILE, log_line, mode="append")
    print("log_error response:", response.status_code, response.text)


def log_other_stuff(username: str, position: str, log_message: str) -> None:
    log_line = "------- " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " - LOG - " + username + " - " + position + " -------"
    log_line += "\n  "+ log_message + "\n\n"
    response = log_to_gist(LOG_TARGET_FILE, log_line, mode="append")
    print("log_other_stuff response:", response.status_code, response.text)

