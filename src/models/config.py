"""
XCA-Bot Configuration Models

This module defines Pydantic models for configuration settings with validation.
"""

import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class TwitterConfig(BaseModel):
    """Twitter API configuration."""
    api_key: str = Field("", description="Twitter API Key")
    api_secret: str = Field("", description="Twitter API Secret")
    access_token: str = Field("", description="Twitter Access Token")
    access_token_secret: str = Field("", description="Twitter Access Token Secret")
    bearer_token: Optional[str] = Field(None, description="Twitter Bearer Token")
    timeout_seconds: int = Field(30, description="Connection timeout in seconds")
    
    @validator('api_key', 'api_secret', 'access_token', 'access_token_secret')
    def must_not_be_empty_for_operation(cls, v, values, **kwargs):
        """Validate that all fields are filled when operations require Twitter API."""
        # We don't enforce non-empty values at init to allow partial configuration
        return v
    
    @classmethod
    def from_env(cls):
        """Create configuration from environment variables."""
        return cls(
            api_key=os.getenv("TWITTER_API_KEY", ""),
            api_secret=os.getenv("TWITTER_API_SECRET", ""),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN", ""),
            access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET", ""),
            bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
            timeout_seconds=int(os.getenv("TWITTER_TIMEOUT_SECONDS", "30"))
        )


class TelegramDestination(BaseModel):
    """Configuration for a Telegram forwarding destination."""
    chat_id: str
    description: Optional[str] = None


class TelegramConfig(BaseModel):
    """Telegram bot configuration."""
    bot_token: str = Field("", description="Telegram Bot Token")
    primary_channel_id: Optional[str] = Field(None, description="Primary Telegram Channel ID")
    forwarding_destinations: List[TelegramDestination] = Field(
        default_factory=list, 
        description="Additional Telegram destinations to forward messages to"
    )
    include_tweet_text: bool = Field(True, description="Include tweet text in notifications")
    timeout_seconds: int = Field(30, description="Connection timeout in seconds")
    
    @classmethod
    def from_env(cls):
        """Create configuration from environment variables."""
        return cls(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            primary_channel_id=os.getenv("TELEGRAM_PRIMARY_CHANNEL_ID"),
            include_tweet_text=os.getenv("TELEGRAM_INCLUDE_TWEET_TEXT", "true").lower() == "true",
            timeout_seconds=int(os.getenv("TELEGRAM_TIMEOUT_SECONDS", "30"))
        )


class DatabaseConfig(BaseModel):
    """Database configuration."""
    connection_string: str = Field("sqlite:///xca_bot.db", description="Database connection string")
    
    @classmethod
    def from_env(cls):
        """Create configuration from environment variables."""
        return cls(
            connection_string=os.getenv("DATABASE_URL", "sqlite:///xca_bot.db")
        )


class MonitoringConfig(BaseModel):
    """Twitter monitoring configuration."""
    check_interval_minutes: int = Field(15, description="Check interval in minutes", ge=1)
    usernames: List[str] = Field(default_factory=list, description="Twitter usernames to monitor")
    regex_patterns: List[str] = Field(
        default_factory=lambda: ["0x[a-fA-F0-9]{40}"],
        description="Regex patterns to match in tweets"
    )
    keywords: List[str] = Field(
        default_factory=lambda: ["contract", "address", "CA", "token"], 
        description="Keywords to match in tweets"
    )
    lookback_hours: int = Field(24, description="How far back to check for tweets on startup")
    max_tweets_per_check: int = Field(20, description="Maximum number of tweets to retrieve per check")
    
    @classmethod
    def from_env(cls):
        """Create configuration from environment variables."""
        # Get comma-separated usernames
        usernames_str = os.getenv("MONITORING_USERNAMES", "")
        usernames = [u.strip() for u in usernames_str.split(",")] if usernames_str else []
        
        # Get comma-separated regex patterns
        patterns_str = os.getenv("MONITORING_REGEX_PATTERNS", "0x[a-fA-F0-9]{40}")
        patterns = [p.strip() for p in patterns_str.split(",")] if patterns_str else ["0x[a-fA-F0-9]{40}"]
        
        # Get comma-separated keywords
        keywords_str = os.getenv("MONITORING_KEYWORDS", "contract,address,CA,token")
        keywords = [k.strip() for k in keywords_str.split(",")] if keywords_str else ["contract", "address", "CA", "token"]
        
        return cls(
            check_interval_minutes=int(os.getenv("MONITORING_CHECK_INTERVAL_MINUTES", "15")),
            usernames=usernames,
            regex_patterns=patterns,
            keywords=keywords,
            lookback_hours=int(os.getenv("MONITORING_LOOKBACK_HOURS", "24")),
            max_tweets_per_check=int(os.getenv("MONITORING_MAX_TWEETS_PER_CHECK", "20"))
        )


class ApplicationConfig(BaseModel):
    """Application-specific configuration."""
    debug_mode: bool = Field(False, description="Enable debug mode")
    timezone: str = Field("UTC", description="Timezone for timestamps")
    log_level: str = Field("INFO", description="Logging level")
    log_file: str = Field("logs/xca_bot.log", description="Path to log file")
    
    @classmethod
    def from_env(cls):
        """Create configuration from environment variables."""
        return cls(
            debug_mode=os.getenv("DEBUG", "false").lower() == "true",
            timezone=os.getenv("TIMEZONE", "UTC"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "logs/xca_bot.log")
        )


class AppConfig(BaseModel):
    """Main application configuration."""
    twitter: TwitterConfig = Field(default_factory=TwitterConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    application: ApplicationConfig = Field(default_factory=ApplicationConfig)
    
    @classmethod
    def from_env(cls):
        """Create configuration from environment variables."""
        return cls(
            twitter=TwitterConfig.from_env(),
            telegram=TelegramConfig.from_env(),
            database=DatabaseConfig.from_env(),
            monitoring=MonitoringConfig.from_env(),
            application=ApplicationConfig.from_env()
        )
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]):
        """Create configuration from a dictionary (loaded from YAML)."""
        return cls(
            twitter=TwitterConfig(**(config_dict.get("twitter", {}) or {})),
            telegram=TelegramConfig(**(config_dict.get("telegram", {}) or {})),
            database=DatabaseConfig(**(config_dict.get("database", {}) or {})),
            monitoring=MonitoringConfig(**(config_dict.get("monitoring", {}) or {})),
            application=ApplicationConfig(**(config_dict.get("application", {}) or {}))
        )
    
    @classmethod
    def from_yaml_and_env(cls, config_dict: Dict[str, Any]):
        """Create configuration by merging YAML and environment variables.
        
        Environment variables take precedence over YAML configuration.
        """
        # First load from YAML
        config = cls.from_dict(config_dict)
        
        # Override with environment variables if they exist
        env_config = cls.from_env()
        
        # Twitter config
        if os.getenv("TWITTER_API_KEY"):
            config.twitter.api_key = env_config.twitter.api_key
        if os.getenv("TWITTER_API_SECRET"):
            config.twitter.api_secret = env_config.twitter.api_secret
        if os.getenv("TWITTER_ACCESS_TOKEN"):
            config.twitter.access_token = env_config.twitter.access_token
        if os.getenv("TWITTER_ACCESS_TOKEN_SECRET"):
            config.twitter.access_token_secret = env_config.twitter.access_token_secret
        if os.getenv("TWITTER_BEARER_TOKEN"):
            config.twitter.bearer_token = env_config.twitter.bearer_token
        if os.getenv("TWITTER_TIMEOUT_SECONDS"):
            config.twitter.timeout_seconds = env_config.twitter.timeout_seconds
        
        # Telegram config
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            config.telegram.bot_token = env_config.telegram.bot_token
        if os.getenv("TELEGRAM_PRIMARY_CHANNEL_ID"):
            config.telegram.primary_channel_id = env_config.telegram.primary_channel_id
        if os.getenv("TELEGRAM_INCLUDE_TWEET_TEXT"):
            config.telegram.include_tweet_text = env_config.telegram.include_tweet_text
        if os.getenv("TELEGRAM_TIMEOUT_SECONDS"):
            config.telegram.timeout_seconds = env_config.telegram.timeout_seconds
        
        # Database config
        if os.getenv("DATABASE_URL"):
            config.database.connection_string = env_config.database.connection_string
        
        # Monitoring config
        if os.getenv("MONITORING_CHECK_INTERVAL_MINUTES"):
            config.monitoring.check_interval_minutes = env_config.monitoring.check_interval_minutes
        if os.getenv("MONITORING_USERNAMES"):
            config.monitoring.usernames = env_config.monitoring.usernames
        if os.getenv("MONITORING_REGEX_PATTERNS"):
            config.monitoring.regex_patterns = env_config.monitoring.regex_patterns
        if os.getenv("MONITORING_KEYWORDS"):
            config.monitoring.keywords = env_config.monitoring.keywords
        if os.getenv("MONITORING_LOOKBACK_HOURS"):
            config.monitoring.lookback_hours = env_config.monitoring.lookback_hours
        if os.getenv("MONITORING_MAX_TWEETS_PER_CHECK"):
            config.monitoring.max_tweets_per_check = env_config.monitoring.max_tweets_per_check
        
        # Application config
        if os.getenv("DEBUG"):
            config.application.debug_mode = env_config.application.debug_mode
        if os.getenv("TIMEZONE"):
            config.application.timezone = env_config.application.timezone
        if os.getenv("LOG_LEVEL"):
            config.application.log_level = env_config.application.log_level
        if os.getenv("LOG_FILE"):
            config.application.log_file = env_config.application.log_file
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the config to a dictionary, masking sensitive fields."""
        config_dict = self.dict(exclude_none=True)
        
        # Mask sensitive information
        if config_dict.get("twitter"):
            for key in ["api_key", "api_secret", "access_token", "access_token_secret", "bearer_token"]:
                if config_dict["twitter"].get(key):
                    value = config_dict["twitter"][key]
                    if len(value) > 8:
                        config_dict["twitter"][key] = f"{value[:4]}...{value[-4:]}"
                    else:
                        config_dict["twitter"][key] = "****"
        
        if config_dict.get("telegram") and config_dict["telegram"].get("bot_token"):
            token = config_dict["telegram"]["bot_token"]
            if len(token) > 8:
                config_dict["telegram"]["bot_token"] = f"{token[:4]}...{token[-4:]}"
            else:
                config_dict["telegram"]["bot_token"] = "****"
        
        # Mask database connection string if it contains credentials
        if config_dict.get("database") and config_dict["database"].get("connection_string"):
            conn_str = config_dict["database"]["connection_string"]
            if "://" in conn_str and "@" in conn_str:
                # Extract parts before and after credentials
                prefix = conn_str.split("://")[0] + "://"
                username_part = conn_str.split("://")[1].split(":")[0]
                suffix = conn_str.split("@")[1]
                config_dict["database"]["connection_string"] = f"{prefix}{username_part}:****@{suffix}"
        
        return config_dict 