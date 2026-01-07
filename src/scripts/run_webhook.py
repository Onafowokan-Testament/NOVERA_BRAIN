import requests

from settings.config import Settings

TELEGRAM_BOT_TOKEN = Settings.TEST_BOT_TOKEN


render_url = "https://c4c6b04ae7fa.ngrok-free.app"
local_url = "https://c37709579c7d.ngrok-free.app"
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
response = requests.post(url, json={"url": f"{local_url}/webhook"})
print(response.json())
