# Crypto Contract Monitor

A tool for monitoring Twitter/X usernames and extracting cryptocurrency contract addresses, sending notifications to Telegram.

## Features

- Monitor Twitter/X accounts for cryptocurrency contract addresses
- Detect Ethereum addresses (0x...) in tweets using regex patterns
- Send formatted results to a Telegram bot/channel
- Forward notifications to multiple Telegram destinations (bots, groups, channels)
- Web interface for configuration and monitoring
- Command-line interface for quick checks and configuration
- Support for scheduled and manual monitoring
- Database storage for matches with CSV export

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+

### Installation

#### Backend Setup

1. Navigate to the backend directory:
```bash
cd twitter-monitor-backend
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your Twitter/X API credentials and Telegram bot token:
   - Create a `.env` file based on `.env.example`
   - Or use the web interface to configure

#### Frontend Setup

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
   - Create a `.env.local` file with:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

## Usage

### Starting the System

<<<<<<< HEAD
1. Start the backend API:
```bash
cd twitter-monitor-backend
python api.py
```
=======
The easiest way to deploy the Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.
>>>>>>> 56b1aed54584d7a2dff998e28bceff21050365fc

2. Start the frontend:
```bash
npm run dev
```

3. Open the web interface at: http://localhost:3000

### CLI Usage

The CLI provides quick access to monitor functions:

```bash
# Check specific usernames for contract addresses
python -m twitter-monitor-backend.cli check vitalik elonmusk

# Add usernames to monitor
python -m twitter-monitor-backend.cli users --add vitalik,elonmusk

# Load usernames from a file
python -m twitter-monitor-backend.cli users --file usernames.txt

# Start monitoring with scheduled checks
python -m twitter-monitor-backend.cli start

# Check status
python -m twitter-monitor-backend.cli status

# Export matches to CSV
python -m twitter-monitor-backend.cli export
```

### Forwarding to External Telegram Destinations

You can forward detected contract addresses to any Telegram channel, group or bot using the chat ID:

#### Using CLI

```bash
# Add a forwarding destination
python -m twitter-monitor-backend.cli telegram --add -1001234567890

# List all configured destinations
python -m twitter-monitor-backend.cli telegram --list

# Remove a destination
python -m twitter-monitor-backend.cli telegram --remove -1001234567890

# Clear all destinations
python -m twitter-monitor-backend.cli telegram --clear
```

#### Using Telegram Bot Commands

If you've set up the Telegram bot, you can also manage destinations through bot commands:

- `/add_destination -1001234567890` - Add a new forwarding destination
- `/list_destinations` - Show all configured destinations
- `/remove_destination -1001234567890` - Remove a destination

#### Finding a Chat ID

To find a Telegram chat ID:
1. Add [@username_to_id_bot](https://t.me/username_to_id_bot) to your group/channel
2. For channels: Forward a message from the channel to the bot
3. For groups: The bot will show the ID when added to the group
4. For users: Forward a message from the user to the bot

Public channels typically have IDs like: `-1001234567890`
Private groups typically have IDs like: `-987654321`
User chat IDs are positive numbers: `123456789`

### Telegram Commands

When configured, the Telegram bot supports these commands:

- `/start` - Welcome message and help
- `/status` - Show monitoring status
- `/check @user1 @user2` - Check specific users immediately
- `/recent [number]` - Show recent matches
- `/add_user @user1 @user2` - Add users to monitor
- `/list_users` - Show all monitored users

## Web Interface

The web interface provides:

- Dashboard with monitoring status
- Configuration for Twitter/X API and Telegram settings
- User-friendly interface to add/remove monitored usernames
- Pattern and keyword management
- Match history with filtering
- Export functionality

## License

This project is licensed under the MIT License - see the LICENSE file for details.
