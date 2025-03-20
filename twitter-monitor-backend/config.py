import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_config():
    """Get configuration from environment variables with fallback to config.json."""
    # Try to load from config.json as fallback
    try:
        with open("config.json", "r") as f:
            config_json = json.load(f)
    except:
        config_json = {
            "twitter": {},
            "telegram": {},
            "monitoring": {
                "usernames": [],
                "regex_patterns": ["0x[a-fA-F0-9]{40}"],
                "keywords": ["pwease", "launch"]
            }
        }
    
    # Twitter configuration
    twitter_config = {
        "api_key": os.getenv("TWITTER_API_KEY", config_json.get("twitter", {}).get("api_key", "")),
        "api_secret": os.getenv("TWITTER_API_SECRET", config_json.get("twitter", {}).get("api_secret", "")),
        "access_token": os.getenv("TWITTER_ACCESS_TOKEN", config_json.get("twitter", {}).get("access_token", "")),
        "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET", config_json.get("twitter", {}).get("access_token_secret", ""))
    }
    
    # Telegram configuration
    telegram_config = {
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", config_json.get("telegram", {}).get("bot_token", "")),
        "channel_id": os.getenv("TELEGRAM_CHANNEL_ID", config_json.get("telegram", {}).get("channel_id", "")),
        "enable_direct_messages": os.getenv("TELEGRAM_ENABLE_DIRECT_MESSAGES", "true").lower() == "true",
        "include_tweet_text": os.getenv("TELEGRAM_INCLUDE_TWEET_TEXT", "true").lower() == "true"
    }
    
    # Monitoring configuration
    try:
        check_interval = int(os.getenv("MONITORING_CHECK_INTERVAL_MINUTES", "15"))
    except:
        check_interval = 15
    
    monitoring_config = {
        "check_interval_minutes": check_interval,
        "usernames": config_json.get("monitoring", {}).get("usernames", []),
        "regex_patterns": config_json.get("monitoring", {}).get("regex_patterns", ["0x[a-fA-F0-9]{40}"]),
        "keywords": config_json.get("monitoring", {}).get("keywords", ["pwease", "launch"])
    }
    
    return {
        "twitter": twitter_config,
        "telegram": telegram_config,
        "monitoring": monitoring_config
    }

def save_config(config):
    """Save configuration to config.json."""
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
    
    return True