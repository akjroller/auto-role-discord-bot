import logging
import os
import signal
import sys
import discord
import requests
from discord.ext import commands, tasks
from role_config import role_assignments
from bot_utils import ensure_roles_exist, assign_roles_to_members, get_days_in_server
from flask import Flask, jsonify
import threading

# Configure logging
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.WARNING,  # Set to WARNING for production
    format=log_format,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),
    ],
)

# Define intents for the bot
intents = discord.Intents.default()
intents.members = True

# Create bot instance with command prefix "!"
bot = commands.Bot(command_prefix="!", intents=intents)

# Gotify settings
GOTIFY_URL = os.getenv("GOTIFY_URL")
GOTIFY_TOKEN = os.getenv("GOTIFY_KEY")

# Flask app for health check
app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for the Flask app.

    Returns:
        A JSON response indicating the status of the bot.
    """
    return jsonify({"status": "healthy"}), 200


def run_flask():
    """
    Starts the Flask app in a separate thread.
    """
    app.run(host="0.0.0.0", port=8015)


# Start the Flask server in a separate thread
threading.Thread(target=run_flask).start()


def send_gotify_notification(title, message, priority=5):
    """
    Sends a notification to the Gotify server.

    Args:
        title (str): The title of the notification.
        message (str): The message content of the notification.
        priority (int): The priority of the notification.
    """
    try:
        response = requests.post(
            f"{GOTIFY_URL}/message?token={GOTIFY_TOKEN}",
            json={"title": title, "message": message, "priority": priority},
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send notification: {e}")


@bot.event
async def on_ready():
    """
    Event handler for when the bot is ready.

    Logs the bot's name and changes the bot's presence.
    """
    logging.info(f"Logged in as {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="Made by awakengaming83"))
    send_gotify_notification(
        "Bot Started", f"Bot {bot.user.name} has started successfully.", priority=10
    )
    check_roles_and_members.start()


@bot.event
async def on_member_join(member):
    """
    Event handler for when a new member joins the guild.

    Assigns the default role to the new member.

    Args:
        member (discord.Member): The member who joined.
    """
    guild = member.guild
    role = discord.utils.get(guild.roles, name="Newbie Loco")
    if role:
        await member.add_roles(role)
        logging.info(f"Assigned role {role.name} to new member {member.name}.")


@tasks.loop(minutes=10)
async def check_roles_and_members():
    """
    Periodic task to check and assign roles to members in all guilds the bot is in.
    """
    for guild in bot.guilds:
        try:
            await ensure_roles_exist(guild, role_assignments)
        except Exception as e:
            logging.error(f"Error ensuring roles exist in guild {guild.name}: {e}")

        try:
            await assign_roles_to_members(guild, role_assignments)
        except Exception as e:
            logging.error(f"Error assigning roles in guild {guild.name}: {e}")


def graceful_shutdown(*args):
    """
    Handles graceful shutdown of the bot.

    Cancels the periodic tasks and stops the event loop.
    """
    logging.info("Shutting down gracefully...")
    check_roles_and_members.cancel()
    bot.loop.stop()
    sys.exit(0)


signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)

# Run the bot using the token from the environment variable
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
