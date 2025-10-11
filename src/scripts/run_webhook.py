import requests

from settings.config import Settings

TELEGRAM_BOT_TOKEN = Settings.BOT_TOKEN


render_url = "https://novera-brain.onrender.com"
local_url = "https://f6731f91f110.ngrok-free.app"
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
response = requests.post(url, json={"url": f"{render_url}/webhook"})
print(response.json())
