import json
import os
import sys
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from colorthief import ColorThief
from io import BytesIO
import base64
import urllib.request
import argparse

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def extract_dominant_color(image_url):
    try:
        with urllib.request.urlopen(image_url) as response:
            image_data = response.read()
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

def get_new_entries(current, previous):
    current_ids = {item['id'] for item in current}
    previous_ids = {item['id'] for item in previous}
    new_entries = [item for item in current if item['id'] not in previous_ids]
    return new_entries

def convert_image_to_base64(image_url):
    try:
        with urllib.request.urlopen(image_url) as response:
            image_data = response.read()
        image = Image.open(BytesIO(image_data))

        background = image.copy()
        background = background.filter(ImageFilter.BoxBlur(2))

        draw = ImageDraw.Draw(background)

        font = ImageFont.truetype("inter.ttf", 150)

        text = "18+"
        text_color = "#F54139"
        outline_color = "#780808"
        outline_width = 5

        draw.text((background.width/2, background.height/2), text, font=font, fill=text_color, stroke_width=outline_width, stroke_fill=outline_color, anchor="mm")

        buffered = BytesIO()
        background.save(buffered, format="PNG")

        return buffered.getvalue()
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        return None

def send_discord_notification(webhook_url, changes, author_icon_url, is_new_data=False):
    for game in changes:
        color = extract_dominant_color(game['thumbnail'])
        if "NSFW" in game["genres"]:
            base64_image = convert_image_to_base64(game['thumbnail'])
            if base64_image is None:
                continue

            payload_json = {
                "content": "",
                "tts": False,
                "embeds": [
                    {
                        "description": f"**{game['subName']}**\n\n{game['description']}",
                        "image": {"url": "attachment://image.png"},
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

            files = {
                'file': ('image.png', BytesIO(base64_image), 'image/png')
            }

            response = requests.post(webhook_url, data={'payload_json': json.dumps(payload_json)}, files=files)
            response.raise_for_status()
        else:
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
                            "icon_url": "https://cdn.discordapp.com/icons/1149479236302802987/8e05d2df735e49167326f43ee4faad45.webp?size=1024&format=webp&width=0&height=256"
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
            headers = {'Content-Type': 'application/json'}
            response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()

def main():
    parser = argparse.ArgumentParser(description='Process game notifications.')
    parser.add_argument('-c', action='store_true', help='Check the length of game names that got changed')
    parser.add_argument('-y', action='store_true', help='Send changed JSON data')
    parser.add_argument('-b', action='store_true', help='Send only new data')
    args = parser.parse_args()

    current_file = 'games.json'
    previous_file = 'previous_games.json'
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    author_icon_url = os.getenv('AUTHOR_ICON_URL')

    current_data = load_json(current_file)
    previous_data = load_json(previous_file)

    if args.c:
        changes = get_changes(current_data, previous_data)
        for game in changes:
            print(f"Game Name Length: {len(game['name'])}")
        sys.exit(0)

    if args.y:
        changes = get_changes(current_data, previous_data)
        if changes:
            send_discord_notification(webhook_url, changes, author_icon_url)
        else:
            print("No changes detected.")
        sys.exit(0)

    if args.b:
        new_entries = get_new_entries(current_data, previous_data)
        if new_entries:
            send_discord_notification(webhook_url, new_entries, author_icon_url, is_new_data=True)
        else:
            print("No new entries detected.")
        sys.exit(0)

    print("No options provided. Use -c, -y, or -b.")
    sys.exit(1)

if __name__ == "__main__":
    main()
