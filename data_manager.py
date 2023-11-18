import yaml
import os
import requests
import json

GIST_ID = os.environ['GIST_ID']
TOKEN = os.environ['TOKEN']
GIST_FILENAME = os.environ['GIST_FILENAME']

headers = {"Authorization": f"token {TOKEN}"}

def fetch_gist_content():
    url = f"https://api.github.com/gists/{GIST_ID}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    gist_data = response.json()
    return gist_data['files'][GIST_FILENAME]['content']

def update_gist(content):
    url = f"https://api.github.com/gists/{GIST_ID}"
    data = {
        "files": {
            GIST_FILENAME: {
                "content": content
            }
        }
    }
    response = requests.patch(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()

def load_data():
    try:
        content = fetch_gist_content()
        return yaml.safe_load(content)
    except Exception as e:
        return {"pinball_machines": [], "players": [], "scores": []}

def save_data(data):
    try:
        content = yaml.dump(data)
        update_gist(content)
    except Exception as e:
        print(f"Error saving data: {e}")