import json
import os
import sys
import requests
from PIL import Image
from colorthief import ColorThief
from io import BytesIO
import urllib.request

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def extract_dominant_color(image_url):
    try:
        with urllib.request.urlopen(image_url) as response:
            image_data = response.read()
        image = Image.open(BytesIO(image_data))
        color_thief = ColorThief(BytesIO(image_data))
        dominant_color = color_thief.get_color(quality=1)
        return '#%02x%02x%02x' % dominant_color
    except Exception as e:
        print(f"Error extracting color: {e}")
        return '#000000'

def get_changes(current, previous):
    current_dict = {item['id']: item for item in current}
    previous_dict = {item['id']: item for item in previous}
    changes = []
    for item_id, item in current_dict.items():
        if item_id not in previous_dict or item != previous_dict[item_id]:
            changes.append(item)
    return changes

def send_discord_notification(webhook_url, changes, author_icon_url):
    headers = {'Content-Type': 'application/json'}

    for game in changes:
        color = extract_dominant_color(game['thumbnail'])
        payload = {
            "content": "",
            "tts": False,
            "embeds": [
                {
                    "description": f"**{game['subName']}**\n\n{game['description']}",
                    "image": { "url": game['thumbnail'] },
                    "title": game['name'],
                    "footer": {
                        "text": "DigitalZone",
                        "icon_url": "https://github.com/god0654/games.json/blob/main/icon.png?raw=true"
                    },
                    "author": {
                        "name": "⎝⎝✧GͥOͣDͫ✧⎠⎠",
                        "url": "https://digitalzone.vercel.app/games",
                        "icon_url": author_icon_url
                    },
                    "url": f"https://digitalzone.vercel.app/games#{game['id']}",
                    "timestamp": game['dateUpdated'],
                    "color": int(color.replace('#', ''), 16)
                }
            ],
            "username": "⎝⎝✧GͥOͣDͫ✧⎠⎠",
            "avatar_url": author_icon_url
        }

        response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

def main():
    current_file = 'games.json'
    previous_file = 'previous_games.json'
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    author_icon_url = os.getenv('AUTHOR_ICON_URL')

    current_data = load_json(current_file)
    previous_data = load_json(previous_file)

    changes = get_changes(current_data, previous_data)

    if changes:
        send_discord_notification(webhook_url, changes, author_icon_url)
    else:
        print("No changes detected.")
        sys.exit(0)

if __name__ == "__main__":
    main()
