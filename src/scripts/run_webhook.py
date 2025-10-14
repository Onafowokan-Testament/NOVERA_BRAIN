import requests

from settings.config import Settings

TELEGRAM_BOT_TOKEN = Settings.BOT_TOKEN


render_url = "https://novera-brain.onrender.com"
local_url = "https://154f2d244fa4.ngrok-free.app"
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
response = requests.post(url, json={"url": f"{local_url}/webhook"})
print(response.json())
