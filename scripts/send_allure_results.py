import os

import requests

# from scripts.send_message import send_message

# TG config
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "8417936478:AAE9JcDPUcw5lKKXEto7qiS_5AR12-pI9-c")
TG_BOT_SEND_MESSAGE_URL = os.getenv(
    "TG_BOT_BASE_URL", f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
)


def send_message(message: str, recipient: str) -> None:
    requests.post(
        url=TG_BOT_SEND_MESSAGE_URL,
        json={"chat_id": recipient, "text": message},
    )


def send_allure_results():
    recipient = os.getenv("NOTIFY_CHANNEL", "@hb_example_notification")
    message = f"test_message from my script {os.getenv('ALLURE_URL', 'default')}"

    send_message(message, recipient)


if __name__ == "__main__":
    send_allure_results()
