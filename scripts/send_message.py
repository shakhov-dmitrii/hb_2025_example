import os

import requests

# TG config
TG_BOT_TOKEN = os.getenv(
    "TG_BOT_TOKEN", "8417936478:AAE9JcDPUcw5lKKXEto7qiS_5AR12-pI9-c"
)
TG_BOT_SEND_MESSAGE_URL = os.getenv(
    "TG_BOT_BASE_URL", f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
)


def send_message(message: str, recipient: str) -> None:
    auth_token = os.getenv("AUTH_TOKEN", "default_token")
    headers = {"Content-Type": "application/json", "Auth": auth_token}
    requests.post(
        url=TG_BOT_SEND_MESSAGE_URL,
        json={"chat_id": recipient, "text": message},
        headers=headers,
    )
