import json
import os
import sys
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from colorthief import ColorThief
from io import BytesIO
import urllib.request

def get_changes(current, previous):
    previous_dict = {item['id']: item for item in previous}
    changes = []

    for item_id, item in {item['id']: item for item in current}.items():
        if item_id not in previous_dict or item['dateUpdated'] != previous_dict[item_id]['dateUpdated']:
            print(f"{'Newly added' if item_id not in previous_dict else 'Changed'} game: {item_id}")
            changes.append(item)

    return changes

def extract_dominant_color(image_url):
    try: return '#%02x%02x%02x' % ColorThief(BytesIO(urllib.request.urlopen(image_url).read())).get_color(quality=1)
    except Exception as e: print(f"Error extracting color: {e}") or '#000000'

def get_image(image_url):
    try: return response.content if (response := requests.get(image_url)).status_code == 200 else print(f"Error fetching image: {response.status_code}") or None
    except Exception as e: return print(f"Error fetching image: {e}") or None

def nsfw(image):
    background = Image.open(BytesIO(image)).filter(ImageFilter.BoxBlur(2))
    ImageDraw.Draw(background).text(
        (background.width / 2, background.height / 2),
        "18+", font=ImageFont.truetype("inter.ttf", 150), fill="#F54139", stroke_width=5, stroke_fill="#780808", anchor="mm"
    )
    with BytesIO() as buffered:
        background.save(buffered, format="PNG")
        return buffered.getvalue()

def send_webhook_notification(webhook_url, games_data, author_image):
    for game in games_data:
        payload = {
            "content": "<@&1287566531861151815>",
            "embeds": [
                {
                    "description": f"**{game['subName']}**\n\n{game['description']}",
                    "image": {"url": "attachment://image.png"},
                    "title": game['name'],
                    "footer": {
                        "text": "DigitalZone",
                        "icon_url": "https://cdn.discordapp.com/icons/1149479236302802987/8e05d2df735e49167326f43ee4faad45.webp?size=1024&format=webp&width=0&height=256"
                    },
                    "author": {
                        "name": "⎝⎝✧GͥOͣDͫ✧⎠⎠",
                        "url": "https://digitalzone.vercel.app/games",
                        "icon_url": author_image
                    },
                    "url": f"https://digitalzone.vercel.app/games#{game['id']}",
                    "timestamp": game['dateUpdated'],
                    "color": int(extract_dominant_color(game['thumbnail']).replace('#', ''), 16),
                    "fields": [
                        {
                            "name": "Genres",
                            "value": game['genres'],
                            "inline": "true"
                        },
                        *([{"name": "CSRINRU", "value": f"[Post]({game['csrinru']})", "inline": "true"}] if game.get('csrinru') else []),
                        *([{"name": "Game link", "value": game['link'], "inline": "true"}] if game.get('link') else [])
                    ]
                }
            ],
            "username": "⎝⎝✧GͥOͣDͫ✧⎠⎠",
            "avatar_url": author_image
        }

        requests.post(webhook_url, data={'payload_json': json.dumps(payload)}, files={
            'file': ('image.png', BytesIO(nsfw(get_image(game['thumbnail'])) if "NSFW" in game["genres"] else get_image(game['thumbnail'])), 'image/png')
        }).raise_for_status()

def main():
    current_file = 'games.json'
    previous_file = 'previous_games.json'
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    author_icon_url = os.getenv('AUTHOR_ICON_URL')

    current_data = json.load(open(current_file, 'r'))
    changes = get_changes(current_data, json.load(open(previous_file, 'r')))

    if changes:
        print(f"Changes detected: {len(changes)}")
        send_webhook_notification(webhook_url, changes, author_icon_url)

        with open(previous_file, 'w') as file:
            json.dump(current_data, file, indent=4)
        sys.exit(0)
    print("No changes detected.")
    sys.exit(0)

if __name__ == "__main__":
    main()
