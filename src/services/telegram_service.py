"""
XCA-Bot Telegram Service

This module provides functionality for sending Telegram notifications.
"""

import asyncio
from typing import List, Dict, Any, Optional
from telegram import Bot
from telegram.error import TelegramError

from src.core.logger import logger, dev_log
from src.models.config import TelegramConfig, TelegramDestination
from src.models.match import TwitterMatch


class TelegramService:
    """Service for sending notifications via Telegram."""
    
    def __init__(self):
        """Initialize Telegram service."""
        self.bot = None
        self.config = None
        self.initialized = False
    
    async def setup(self, config: TelegramConfig) -> bool:
        """Set up Telegram bot.
        
        Args:
            config: Telegram configuration
            
        Returns:
            bool: True if setup was successful
        """
        try:
            if not config.bot_token:
                logger.error("Telegram bot token is missing")
                return False
                
            # Initialize bot
            self.bot = Bot(token=config.bot_token)
            
            # Test connection by getting bot info
            bot_info = await self.bot.get_me()
            logger.info(f"Telegram bot connected: @{bot_info.username}")
            
            self.config = config
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            self.initialized = False
            return False
    
    async def send_notification(
        self, 
        match: TwitterMatch, 
        include_tweet_text: bool = True
    ) -> Dict[str, bool]:
        """Send notification about a Twitter match to configured destinations.
        
        Args:
            match: TwitterMatch object with contract address info
            include_tweet_text: Whether to include the tweet text in the message
            
        Returns:
            Dict with destination chat_ids as keys and success status as values
        """
        if not self.initialized or not self.bot:
            logger.error("Telegram bot not initialized")
            return {}
        
        # Format message
        message = match.to_message(include_tweet_text=include_tweet_text)
        
        results = {}
        destinations = []
        
        # Add primary channel if configured
        if self.config.primary_channel_id:
            destinations.append({"chat_id": self.config.primary_channel_id, "is_primary": True})
        
        # Add forwarding destinations
        for dest in self.config.forwarding_destinations:
            destinations.append({"chat_id": dest.chat_id, "is_primary": False})
        
        # Send to all destinations
        for dest in destinations:
            chat_id = dest["chat_id"]
            is_primary = dest["is_primary"]
            
            try:
                # Send message
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    disable_web_page_preview=False,
                    parse_mode=None  # Plain text to avoid parsing issues with addresses
                )
                
                logger.info(f"Sent notification to Telegram chat {chat_id}")
                if is_primary:
                    dev_log(f"Sent contract address match for @{match.username} to primary Telegram channel", "INFO")
                
                results[chat_id] = True
                
            except TelegramError as e:
                logger.error(f"Failed to send notification to Telegram chat {chat_id}: {e}")
                results[chat_id] = False
        
        return results
    
    async def send_system_message(self, message: str, alert: bool = False) -> bool:
        """Send a system message to the primary channel.
        
        Args:
            message: Message text
            alert: Whether this is an alert message
            
        Returns:
            bool: True if message was sent successfully
        """
        if not self.initialized or not self.bot:
            logger.error("Telegram bot not initialized")
            return False
        
        if not self.config.primary_channel_id:
            logger.warning("No primary channel configured for system messages")
            return False
        
        prefix = "🚨 ALERT" if alert else "ℹ️ INFO"
        formatted_message = f"{prefix}: {message}"
        
        try:
            await self.bot.send_message(
                chat_id=self.config.primary_channel_id,
                text=formatted_message,
                disable_web_page_preview=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send system message: {e}")
            return False
    
    async def test_destination(self, chat_id: str) -> bool:
        """Test if a destination is valid and the bot can send messages to it.
        
        Args:
            chat_id: Telegram chat ID to test
            
        Returns:
            bool: True if test message was sent successfully
        """
        if not self.initialized or not self.bot:
            logger.error("Telegram bot not initialized")
            return False
        
        try:
            test_message = (
                "🧪 Test Message\n\n"
                "This is a test message from XCA-Bot to verify this destination "
                "is configured correctly for receiving cryptocurrency contract addresses."
            )
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=test_message,
                disable_web_page_preview=True
            )
            
            logger.info(f"Successfully sent test message to {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send test message to {chat_id}: {e}")
            return False 