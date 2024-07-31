import os
import requests

# Define the Gotify server URL and token
GOTIFY_URL = os.getenv("GOTIFY_URL")
GOTIFY_TOKEN = os.getenv("GOTIFY_KEY")
BOT_URL = "http://localhost:8015/health"


def send_gotify_notification(message):
    """
    Sends a notification to the Gotify server.

    Args:
        message (str): The message content of the notification.
    """
    try:
        response = requests.post(
            f"{GOTIFY_URL}/message?token={GOTIFY_TOKEN}",
            json={"message": message, "title": "Bot Health Check", "priority": 10},
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send notification: {e}")


def check_bot_health():
    """
    Checks the health of the bot by making a request to the health endpoint.

    If the bot is not healthy, sends a notification to the Gotify server.
    """
    try:
        response = requests.get(BOT_URL)
        if response.status_code == 200:
            print("Bot is healthy")
        else:
            print("Bot is not healthy")
            send_gotify_notification(
                f"Bot health check failed with status code {response.status_code}"
            )
    except requests.exceptions.RequestException as e:
        print("Bot health check failed")
        send_gotify_notification(f"Bot health check failed: {e}")


if __name__ == "__main__":
    check_bot_health()
