# XCA-Bot: Cryptocurrency Address Monitor

XCA-Bot is a sophisticated system for monitoring Twitter/X accounts for cryptocurrency contract addresses and forwarding them to Telegram channels or groups.

## Features

- 🔍 **Twitter Monitoring**: Continuously monitor specified Twitter usernames for new tweets
- 🔢 **Contract Address Detection**: Extract cryptocurrency contract addresses using regex patterns
- 📱 **Telegram Notifications**: Send notifications about found addresses to Telegram channels/groups
- 🔄 **Multiple Destinations**: Support for multiple Telegram forwarding destinations
- 📊 **API Access**: RESTful API for controlling the service and retrieving data
- 💾 **Persistent Storage**: Database storage for matched addresses and configuration
- 📝 **Comprehensive Logging**: Detailed logs for troubleshooting and operations

## System Requirements

- Python 3.8 or higher
- Twitter API credentials (developer account)
- Telegram Bot Token
- Database (SQLite or PostgreSQL)

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/xca-bot.git
cd xca-bot
```

2. **Create and activate a virtual environment**

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

```bash
# On Linux/Mac
bash setup_env.sh
# On Windows
copy .env.example .env
```

Then edit the `.env` file with your API keys and configuration.

## Configuration

XCA-Bot can be configured using either:

1. **Environment Variables** (recommended for sensitive data)
2. **YAML Configuration File** (for more complex settings)
3. **A combination of both** (env vars take precedence)

### Environment Variables

Edit the `.env` file with your specific settings:

```
# Twitter API Credentials
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_PRIMARY_CHANNEL_ID=-1001234567890

# Database Configuration
DATABASE_URL=sqlite:///xca_bot.db

# Monitoring Configuration
MONITORING_USERNAMES=username1,username2,username3
MONITORING_CHECK_INTERVAL_MINUTES=5
```

### YAML Configuration

For more complex settings, you can use a YAML file:

```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your settings
```

**Note**: Values in the `.env` file will override those in the YAML config file.

## Usage

### Starting the Service

```bash
# Using only environment variables
python main.py

# Using a config file (environment vars still apply)
python main.py --config config.yaml
```

Additional command-line options:
- `--auto-start`: Start monitoring automatically
- `--host`: API server host (default: from API_HOST env var or 127.0.0.1)
- `--port`: API server port (default: from API_PORT env var or 8000)

### API Endpoints

The service exposes a RESTful API at `http://host:port/api/v1`:

- `GET /status` - Get current monitoring status
- `POST /start` - Start monitoring
- `POST /stop` - Stop monitoring
- `POST /check` - Immediate check for contract addresses
- `GET /matches` - Get recent matches
- `GET /config` - Get current configuration
- `POST /config/telegram/destinations` - Add a Telegram destination
- `DELETE /config/telegram/destinations/{chat_id}` - Remove a Telegram destination
- `POST /config/telegram/test/{chat_id}` - Test a Telegram destination

API documentation is available at `http://host:port/docs`

## System Architecture

XCA-Bot consists of several core components:

1. **Twitter Service**: Handles Twitter API interactions and tweet scanning
2. **Telegram Service**: Manages Telegram bot communication
3. **Monitor Service**: Coordinates the monitoring process
4. **Database Repository**: Stores matches and configuration
5. **FastAPI Application**: Provides RESTful API access

## Development

### Project Structure

```
xca-bot/
├── main.py                  # Main entry point
├── .env                     # Environment variables (not committed to git)
├── .env.example             # Example environment variables
├── config.example.yaml      # Example YAML configuration
├── requirements.txt         # Dependencies
├── src/
│   ├── api/                 # API components
│   │   ├── app.py           # FastAPI application
│   │   └── routes.py        # API routes
│   ├── core/                # Core components
│   │   ├── logger.py        # Logging utilities
│   │   └── monitor.py       # Main monitor service
│   ├── models/              # Data models
│   │   ├── config.py        # Configuration models
│   │   └── match.py         # Match data models
│   ├── db/                  # Data access
│   │   ├── models.py        # Database models
│   │   └── repository.py    # Database access
│   └── services/            # Service components
│       ├── telegram_service.py  # Telegram functionality
│       └── twitter_service.py   # Twitter functionality
└── logs/                    # Log files
```

### Testing

Run the test suite with:

```bash
pytest tests/
```

## Troubleshooting

- Check the log files in the `logs/` directory
- Ensure your Twitter API credentials are valid
- Verify your Telegram bot has permission to send messages to the configured channels
- Check that your `.env` file contains the correct values

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Tweepy](https://www.tweepy.org/) for Twitter API access
- [python-telegram-bot](https://python-telegram-bot.org/) for Telegram interactions
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for database ORM 