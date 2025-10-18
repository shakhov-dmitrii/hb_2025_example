import os

import requests

# from scripts.send_message import send_message

# TG config
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "default")
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


def send_allure_results():
    recipient = os.getenv("NOTIFY_CHANNEL", "@hb_example_notification")
    message = f"test_message from my script {os.getenv('ALLURE_URL', 'default')}"

    send_message(message, recipient)


if __name__ == "__main__":
    send_allure_results()
