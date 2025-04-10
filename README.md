# XCA-Bot: Cryptocurrency Address Monitor

XCA-Bot is a sophisticated system for monitoring Twitter/X accounts for cryptocurrency contract addresses and forwarding them to Telegram channels or groups. It includes both a backend service and a modern web dashboard.

## Features

- 🔍 **Twitter Monitoring**: Continuously monitor specified Twitter usernames for new tweets
- 🔢 **Contract Address Detection**: Extract cryptocurrency contract addresses using regex patterns
- 📊 **Ticker Symbol Detection**: Identify cryptocurrency ticker symbols (like $BTC, $ETH)
- 📱 **Telegram Notifications**: Send notifications about found addresses to Telegram channels/groups
- 🔄 **Multiple Destinations**: Support for multiple Telegram forwarding destinations
- 🖥️ **Web Dashboard**: Modern Next.js web interface for easy monitoring and configuration
- 📊 **API Access**: RESTful API for controlling the service and retrieving data
- 💾 **Persistent Storage**: Database storage for matched addresses and configuration
- 📝 **Comprehensive Logging**: Detailed logs for troubleshooting and operations

## System Architecture

XCA-Bot consists of two main components:

1. **Backend Service** (Python):
   - Twitter/X API integration
   - Cryptocurrency address detection
   - Telegram notification service
   - Database storage
   - RESTful API

2. **Web Dashboard** (Next.js):
   - Real-time monitoring status
   - Contract address viewing
   - Configuration management
   - Username monitoring settings
   - Telegram destination management

## System Requirements

- Python 3.8 or higher
- Node.js 14.x or higher
- Twitter API credentials (developer account)
- Telegram Bot Token
- Database (SQLite or PostgreSQL)

## Backend Installation

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

## Frontend Installation

1. **Install frontend dependencies**

```bash
cd app
npm install
```

2. **Configure API connection**

The frontend automatically connects to the backend API at `http://localhost:8000/api/v1`. To change this, set the `NEXT_PUBLIC_API_BASE_URL` environment variable or edit the configuration in `app/lib/api.js`.

## Configuration

XCA-Bot can be configured using either:

1. **Environment Variables** (recommended for sensitive data)
2. **YAML Configuration File** (for more complex settings)
3. **A combination of both** (env vars take precedence)
4. **Web Dashboard** (for most settings)

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

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Monitoring Configuration
MONITORING_USERNAMES=username1,username2,username3
MONITORING_CHECK_INTERVAL_MINUTES=5

# Frontend Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

### YAML Configuration

For more complex settings, you can use a YAML file:

```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your settings
```

**Note**: Values in the `.env` file will override those in the YAML config file.

## Running the Application

### Starting the Backend Service

```bash
# From the project root directory
python main.py
```

Additional command-line options:
- `--auto-start`: Start monitoring automatically
- `--config`: Path to YAML config file
- `--host`: API server host (default: from API_HOST env var or 127.0.0.1)
- `--port`: API server port (default: from API_PORT env var or 8000)

### Starting the Web Dashboard (Development)

```bash
# From the app directory
npm run dev
```

The dashboard will be available at http://localhost:3000

### Production Deployment

For production deployment, build the frontend:

```bash
# From the app directory
npm run build
npm start
```

For the backend, consider using a process manager like supervisor, systemd, or PM2.

## API Endpoints

The service exposes a RESTful API at `http://host:port/api/v1`:

- `GET /status` - Get current monitoring status
- `POST /monitoring/start` - Start monitoring
- `POST /monitoring/stop` - Stop monitoring
- `POST /monitoring/check-now` - Immediate check for contract addresses
- `GET /matches` - Get recent matches
- `GET /config` - Get current configuration
- `PUT /config` - Update configuration
- `POST /telegram/destinations` - Add a Telegram destination
- `DELETE /telegram/destinations/{chat_id}` - Remove a Telegram destination
- `POST /telegram/destinations/{chat_id}/test` - Test a Telegram destination

API documentation is available at `http://host:port/docs`

## Project Structure

```
xca-bot/
├── main.py                  # Main entry point
├── .env                     # Environment variables (not committed to git)
├── .env.example             # Example environment variables
├── config.example.yaml      # Example YAML configuration
├── requirements.txt         # Dependencies
├── app/                     # Web dashboard (Next.js)
│   ├── components/          # React components
│   ├── lib/                 # API client and utilities
│   ├── pages/               # Next.js pages
│   ├── public/              # Static assets
│   ├── styles/              # CSS styles
│   └── package.json         # Frontend dependencies
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

## Troubleshooting

### Backend Issues

- Check the log files in the `logs/` directory
- Ensure your Twitter API credentials are valid
- Verify your Telegram bot has permission to send messages
- Check that your `.env` file contains the correct values

### Frontend Issues

- Check browser console for errors
- Ensure the backend API is running
- Verify the API URL is set correctly
- Try clearing browser cache

### Common Solutions

- **API Connection Failures**: Make sure the backend is running and the API URL is correct
- **Twitter API Errors**: Verify your Twitter credentials and permissions
- **Telegram Errors**: Ensure your bot token is valid and the bot has admin permissions in the channel

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Tweepy](https://www.tweepy.org/) for Twitter API access
- [python-telegram-bot](https://python-telegram-bot.org/) for Telegram interactions
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- [Next.js](https://nextjs.org/) for the web dashboard
- [React](https://reactjs.org/) for the frontend user interface
- [SQLAlchemy](https://www.sqlalchemy.org/) for database ORM 