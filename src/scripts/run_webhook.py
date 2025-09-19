import requests

from settings.config import Settings

TELEGRAM_BOT_TOKEN = Settings.BOT_TOKEN


render_url = "https://novera.onrender.com"
local_url = "https://7f110baa65a6.ngrok-free.app"
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
response = requests.post(url, json={"url": f"{local_url}/webhook"})
print(response.json())
