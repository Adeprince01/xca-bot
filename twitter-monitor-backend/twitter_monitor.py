import os
import re
import time
import json
import logging
import sqlite3
import schedule
import requests
from datetime import datetime
import tweepy
from telegram import Bot
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("twitter_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TwitterMonitor:
    def __init__(self, config_file="config.json"):
        """Initialize the Twitter Monitor with configuration."""
        self.config = self.load_config(config_file)
        self.apply_env_overrides()  # Apply environment variables over config values
        self.setup_twitter_api()
        self.setup_telegram_bot()
        self.setup_database()
        self.running = False
        
    def load_config(self, config_file):
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_file}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Create default config if file doesn't exist
            default_config = {
                "twitter": {
                    "api_key": "",
                    "api_secret": "",
                    "access_token": "",
                    "access_token_secret": ""
                },
                "telegram": {
                    "bot_token": "",
                    "channel_id": "",
                    "forwarding_destinations": [],
                    "enable_direct_messages": True,
                    "include_tweet_text": True
                },
                "monitoring": {
                    "check_interval_minutes": 15,
                    "usernames": [],
                    "regex_patterns": ["0x[a-fA-F0-9]{40}"],  # Ethereum address pattern
                    "keywords": ["contract", "address", "CA", "token", "launch", "airdrop", "presale", "blockchain"]
                }
            }
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            logger.info(f"Created default configuration file: {config_file}")
            return default_config
    
    def apply_env_overrides(self):
        """Apply environment variables to override configuration."""
        # Twitter API credentials
        twitter_api_key = os.getenv("TWITTER_API_KEY")
        if twitter_api_key:
            self.config["twitter"]["api_key"] = twitter_api_key
            
        twitter_api_secret = os.getenv("TWITTER_API_SECRET")
        if twitter_api_secret:
            self.config["twitter"]["api_secret"] = twitter_api_secret
            
        twitter_access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        if twitter_access_token:
            self.config["twitter"]["access_token"] = twitter_access_token
            
        twitter_access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        if twitter_access_token_secret:
            self.config["twitter"]["access_token_secret"] = twitter_access_token_secret
        
        # Telegram configuration
        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if telegram_bot_token:
            self.config["telegram"]["bot_token"] = telegram_bot_token
            
        telegram_channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
        if telegram_channel_id:
            self.config["telegram"]["channel_id"] = telegram_channel_id
        
        # Check interval
        check_interval = os.getenv("MONITORING_CHECK_INTERVAL_MINUTES")
        if check_interval and check_interval.isdigit():
            self.config["monitoring"]["check_interval_minutes"] = int(check_interval)
        
        # Ensure forwarding_destinations exists
        if "forwarding_destinations" not in self.config["telegram"]:
            self.config["telegram"]["forwarding_destinations"] = []
        
        # Log the override status
        logger.info("Applied environment variable overrides to configuration")
    
    def save_config(self, config_file="config.json"):
        """Save current configuration to JSON file."""
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def setup_twitter_api(self):
        """Set up Twitter API client."""
        try:
            auth = tweepy.OAuth1UserHandler(
                self.config["twitter"]["api_key"],
                self.config["twitter"]["api_secret"],
                self.config["twitter"]["access_token"],
                self.config["twitter"]["access_token_secret"]
            )
            self.twitter_api = tweepy.API(auth)
            # Test the credentials
            self.twitter_api.verify_credentials()
            logger.info("Twitter API credentials verified successfully")
        except Exception as e:
            logger.error(f"Error setting up Twitter API: {e}")
            self.twitter_api = None
    
    def setup_telegram_bot(self):
        """Set up Telegram bot."""
        try:
            token = self.config["telegram"]["bot_token"]
            if not token:
                logger.error("Telegram bot token is missing")
                self.telegram_bot = None
                return
                
            self.telegram_bot = Bot(token=token)
            # Don't try to get bot info, which requires await
            logger.info(f"Telegram bot initialized with token: {token[:5]}...{token[-5:] if len(token) > 10 else ''}")
        except Exception as e:
            logger.error(f"Error setting up Telegram bot: {e}")
            self.telegram_bot = None
    
    def setup_database(self):
        """Set up SQLite database for storing matches."""
        try:
            self.conn = sqlite3.connect('twitter_monitor.db', check_same_thread=False)
            self.cursor = self.conn.cursor()
            
            # Create tables if they don't exist
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    tweet_id TEXT,
                    tweet_text TEXT,
                    matched_pattern TEXT,
                    timestamp DATETIME,
                    sent_to_telegram BOOLEAN
                )
            ''')
            self.conn.commit()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            self.conn = None
    
    def check_tweets(self):
        """Check tweets from monitored users for matches."""
        if not self.twitter_api:
            logger.error("Twitter API not configured properly")
            return
        
        usernames = self.config["monitoring"]["usernames"]
        if not usernames:
            logger.warning("No usernames configured for monitoring")
            return
        
        logger.info(f"Checking {len(usernames)} users for updates")
        
        # Compile regex patterns
        patterns = []
        for pattern in self.config["monitoring"]["regex_patterns"]:
            try:
                patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.error(f"Invalid regex pattern '{pattern}': {e}")
        
        # Prepare keywords
        keywords = [kw.lower() for kw in self.config["monitoring"]["keywords"]]
        
        # Check each user's timeline
        for username in usernames:
            try:
                # Remove @ if present
                clean_username = username.replace('@', '')
                
                # Get user's recent tweets
                tweets = self.twitter_api.user_timeline(
                    screen_name=clean_username,
                    count=10,  # Limit to recent tweets
                    tweet_mode="extended"
                )
                
                # Process each tweet
                for tweet in tweets:
                    tweet_id = tweet.id_str
                    tweet_text = tweet.full_text
                    
                    # Skip if we've already processed this tweet
                    if self.is_tweet_processed(tweet_id):
                        continue
                    
                    # Check for matches
                    matched_patterns = []
                    
                    # Check regex patterns
                    for pattern in patterns:
                        if pattern.search(tweet_text):
                            matched_patterns.append(pattern.pattern)
                    
                    # Check keywords
                    for keyword in keywords:
                        if keyword in tweet_text.lower():
                            matched_patterns.append(keyword)
                    
                    if matched_patterns:
                        logger.info(f"Found match in @{clean_username} tweet")
                        
                        # Store in database
                        self.store_match(clean_username, tweet_id, tweet_text, matched_patterns)
                        
                        # Send to Telegram
                        self.send_to_telegram(clean_username, tweet_id, tweet_text, matched_patterns)
                
                # Respect rate limits
                time.sleep(1)
                
            except tweepy.TooManyRequests:
                logger.error("Twitter API rate limit exceeded")
                # Wait before continuing
                time.sleep(60)
                break
            except tweepy.Unauthorized:
                logger.error(f"Unauthorized for user {username}. Check credentials.")
            except Exception as e:
                logger.error(f"Error processing tweets for {username}: {e}")
    
    def is_tweet_processed(self, tweet_id):
        """Check if a tweet has already been processed."""
        try:
            self.cursor.execute("SELECT id FROM matches WHERE tweet_id = ?", (tweet_id,))
            return self.cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Database error checking tweet: {e}")
            return False
    
    def store_match(self, username, tweet_id, tweet_text, matched_patterns):
        """Store a match in the database."""
        try:
            self.cursor.execute(
                "INSERT INTO matches (username, tweet_id, tweet_text, matched_pattern, timestamp, sent_to_telegram) VALUES (?, ?, ?, ?, ?, ?)",
                (username, tweet_id, tweet_text, json.dumps(matched_patterns), datetime.now().isoformat(), False)
            )
            self.conn.commit()
            logger.info(f"Stored match from @{username} in database")
        except Exception as e:
            logger.error(f"Error storing match in database: {e}")
    
    def send_to_telegram(self, username, tweet_id, tweet_text, matched_patterns):
        """Send a match to Telegram."""
        if not self.telegram_bot:
            logger.error("Telegram bot not configured properly")
            return
        
        try:
            # Create message
            tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
            
            # Extract contract addresses from the tweet text
            contract_addresses = []
            for pattern in matched_patterns:
                if pattern == "0x[a-fA-F0-9]{40}":  # This is our Ethereum address pattern
                    # Find all matches in the tweet text
                    addresses = re.findall(r"0x[a-fA-F0-9]{40}", tweet_text)
                    contract_addresses.extend(addresses)
            
            # Create crypto-specific message format
            message = f"Username: @{username}\n"
            
            # Add contract addresses if found
            if contract_addresses:
                message += f"Contract: {', '.join(contract_addresses)}\n"
            else:
                message += "No CA found\n"
            
            # Add tweet text if configured
            if self.config["telegram"]["include_tweet_text"]:
                message += f"Tweet: {tweet_text}\n"
            
            message += f"Link: {tweet_url}\n"
            message += f"Time: {timestamp}"
            
            # Send to primary channel
            sent_successfully = False
            channel_id = self.config["telegram"]["channel_id"]
            if channel_id:
                try:
                    self.telegram_bot.send_message(
                        chat_id=channel_id,
                        text=message,
                        disable_web_page_preview=False
                    )
                    sent_successfully = True
                    logger.info(f"Sent notification to primary Telegram channel for @{username}")
                except Exception as e:
                    logger.error(f"Error sending to primary Telegram channel: {e}")
            
            # Send to additional configured destinations
            forwarding_destinations = self.config["telegram"].get("forwarding_destinations", [])
            for destination in forwarding_destinations:
                dest_chat_id = destination.get("chat_id")
                if dest_chat_id:
                    try:
                        self.telegram_bot.send_message(
                            chat_id=dest_chat_id,
                            text=message,
                            disable_web_page_preview=False
                        )
                        sent_successfully = True
                        logger.info(f"Forwarded notification to {dest_chat_id} for @{username}")
                    except Exception as e:
                        logger.error(f"Error forwarding to Telegram destination {dest_chat_id}: {e}")
            
            # Update database
            if sent_successfully:
                self.cursor.execute(
                    "UPDATE matches SET sent_to_telegram = ? WHERE tweet_id = ?",
                    (True, tweet_id)
                )
                self.conn.commit()
                
            return sent_successfully
        except Exception as e:
            logger.error(f"Error sending to Telegram: {e}")
            return False
    
    def start_monitoring(self):
        """Start the monitoring process."""
        if self.running:
            logger.warning("Monitoring is already running")
            return
        
        if not self.twitter_api or not self.telegram_bot:
            logger.error("Cannot start monitoring: Twitter API or Telegram bot not configured")
            return
        
        self.running = True
        logger.info("Monitoring started")
        
        # Run immediately
        self.check_tweets()
        
        # Schedule regular checks
        interval = self.config["monitoring"]["check_interval_minutes"]
        schedule.every(interval).minutes.do(self.check_tweets)
        
        # Keep running until stopped
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def stop_monitoring(self):
        """Stop the monitoring process."""
        self.running = False
        logger.info("Monitoring stopped")
    
    def update_usernames(self, usernames):
        """Update the list of usernames to monitor."""
        if isinstance(usernames, str):
            # Split by commas if string
            usernames = [u.strip() for u in usernames.split(',')]
        
        self.config["monitoring"]["usernames"] = usernames
        self.save_config()
        logger.info(f"Updated usernames list: {len(usernames)} users")
    
    def update_patterns(self, patterns):
        """Update the regex patterns to match."""
        if isinstance(patterns, str):
            # Split by newlines if string
            patterns = [p.strip() for p in patterns.split('\n') if p.strip()]
        
        self.config["monitoring"]["regex_patterns"] = patterns
        self.save_config()
        logger.info(f"Updated regex patterns: {len(patterns)} patterns")
    
    def update_keywords(self, keywords):
        """Update the keywords to match."""
        if isinstance(keywords, str):
            # Split by newlines if string
            keywords = [k.strip() for k in keywords.split('\n') if k.strip()]
        
        self.config["monitoring"]["keywords"] = keywords
        self.save_config()
        logger.info(f"Updated keywords: {len(keywords)} keywords")
    
    def get_recent_matches(self, limit=10):
        """Get recent matches from the database."""
        try:
            self.cursor.execute(
                "SELECT username, tweet_id, tweet_text, matched_pattern, timestamp FROM matches ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            matches = []
            for row in self.cursor.fetchall():
                username, tweet_id, tweet_text, matched_pattern, timestamp = row
                matches.append({
                    "username": f"@{username}",
                    "tweet_id": tweet_id,
                    "tweet_text": tweet_text,
                    "matched_pattern": json.loads(matched_pattern),
                    "timestamp": timestamp,
                    "tweet_url": f"https://twitter.com/{username}/status/{tweet_id}"
                })
            return matches
        except Exception as e:
            logger.error(f"Error getting recent matches: {e}")
            return []
    
    def export_matches_csv(self, filename="matches_export.csv"):
        """Export matches to CSV file."""
        try:
            self.cursor.execute(
                "SELECT username, tweet_id, tweet_text, matched_pattern, timestamp FROM matches ORDER BY timestamp DESC"
            )
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                f.write("Username,Tweet ID,Tweet Text,Matched Pattern,Timestamp,Tweet URL\n")
                for row in self.cursor.fetchall():
                    username, tweet_id, tweet_text, matched_pattern, timestamp = row
                    tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
                    # Escape CSV special characters
                    tweet_text = tweet_text.replace('"', '""')
                    matched_pattern_str = json.dumps(json.loads(matched_pattern)).replace('"', '""')
                    
                    f.write(f'"{username}","{tweet_id}","{tweet_text}","{matched_pattern_str}","{timestamp}","{tweet_url}"\n')
            
            logger.info(f"Exported {self.cursor.rowcount} matches to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error exporting matches to CSV: {e}")
            return None
    
    def cleanup_database(self):
        """Compact the database by removing old entries."""
        try:
            # Keep only the last 1000 entries
            self.cursor.execute(
                "DELETE FROM matches WHERE id NOT IN (SELECT id FROM matches ORDER BY timestamp DESC LIMIT 1000)"
            )
            deleted_rows = self.cursor.rowcount
            self.conn.commit()
            
            # Vacuum the database to reclaim space
            self.conn.execute("VACUUM")
            
            logger.info(f"Database cleanup: removed {deleted_rows} old entries")
            return deleted_rows
        except Exception as e:
            logger.error(f"Error cleaning up database: {e}")
            return 0
    
    def close(self):
        """Close database connection and cleanup."""
        if self.conn:
            self.conn.close()
        logger.info("Twitter Monitor shutdown")


def main():
    """Main entry point for the application."""
    monitor = TwitterMonitor()
    
    # Check if configuration is complete
    if (not monitor.config["twitter"]["api_key"] or 
        not monitor.config["telegram"]["bot_token"]):
        logger.error("Configuration incomplete. Please edit config.json")
        print("Configuration incomplete. Please edit config.json with your API keys.")
        return
    
    try:
        print("Twitter/X Monitor started. Press Ctrl+C to stop.")
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
        monitor.stop_monitoring()
    finally:
        monitor.close()


if __name__ == "__main__":
    main()