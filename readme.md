# Auto Role Discord Bot

The Auto Role Discord Bot manages and assigns roles to server members based on their duration in the server. Features include automatic role management, batch processing, retry logic for rate limits, health checks with Flask, and notifications via Gotify. Easily deployable with Docker.

## Features

- **Automatic Role Management**: Assign roles based on the number of days a member has been in the server.
- **Batch Processing**: Efficiently processes members in batches to handle large servers.
- **Retry Logic**: Handles Discord API rate limits with retry logic.
- **Health Checks**: Integrated health check using Flask.
- **Gotify Notifications**: Sends notifications for important events and health status.

## Setup

### Prerequisites

- Docker and Docker Compose installed.
- A Discord bot token.
- Gotify server URL and token.

### Environment Variables

Create an `.env` file in the project root with the following variables:

```sh
DISCORD_BOT_TOKEN=your_discord_bot_token
GOTIFY_URL=your_gotify_server_url
GOTIFY_KEY=your_gotify_token
```

### Role Configuration

Create an `example_role_config.py` file in the project root with the role assignments configuration:

# Example configuration for role assignments based on the number of days in the server

```python
role_assignments = [
{"days": 0, "role_name": "New Member"}, # 0 days (default for new members)
{"days": 30, "role_name": "Member"}, # 1 month
{"days": 180, "role_name": "Veteran Member"}, # 6 months
{"days": 365, "role_name": "Senior Member"}, # 1 year
]
```

### Docker Setup

Build and run the bot using Docker Compose:

```sh
docker-compose up --build
```

## Usage

The bot will start automatically and perform the following actions:

- Check and create roles if they do not exist.
- Assign roles to members based on their join date.
- Send notifications via Gotify.
- Provide health check endpoint at `http://localhost:8015/health`.

## Development

### Local Setup

1. Clone the repository:

```sh
git clone https://github.com/akjroller/auto-role-discord-bot
cd auto-role-discord-bot
```

2. Create a virtual environment and install dependencies:

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Create the `.env` and `role_config.py` files as described above.

4. Run the bot locally:

```python
python bot.py
```

### Code Structure

- **bot.py**: Main entry point for the bot.
- **bot_utils.py**: Utility functions for role management.
- **health_check.py**: Script for health checking.
- **role_config.py**: Role assignments configuration.

## Contributing

Feel free to open issues or submit pull requests if you have suggestions or improvements.
