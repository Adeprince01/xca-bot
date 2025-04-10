"""
XCA-Bot Monitor Core

This module coordinates Twitter monitoring and Telegram notifications.
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from src.core.logger import logger, dev_log
from src.models.config import AppConfig
from src.models.match import TwitterMatch
from src.services.twitter_service import TwitterService
from src.services.telegram_service import TelegramService
from src.db.repository import DatabaseRepository


class MonitorService:
    """Core service for coordinating Twitter monitoring and Telegram notifications."""
    
    def __init__(self):
        """Initialize the monitor service."""
        self.twitter_service = TwitterService()
        self.telegram_service = TelegramService()
        self.db_repo = None
        
        self.config = None
        self.initialized = False
        self._running = False
        self._task = None
        
        # Service status tracking
        self.status = {
            "database": False,
            "twitter": False,
            "telegram": False,
            "last_error": None
        }
        
        # Event listeners for match events
        self.on_match_callbacks = []
    
    async def init(self, config: AppConfig, max_retries: int = 3) -> bool:
        """Initialize services with configuration.
        
        Args:
            config: Application configuration
            max_retries: Maximum number of database connection retries
            
        Returns:
            bool: True if initialization was successful
        """
        dev_log("Initializing core monitoring service", "INFO")
        self.config = config
        
        # Initialize database repository with retries
        self.db_repo = DatabaseRepository(db_url=config.database.connection_string)
        
        # Initialize database with retries
        for attempt in range(max_retries):
            try:
                await self.db_repo.init_db()
                self.status["database"] = True
                dev_log("Database initialized", "DONE")
                break
            except Exception as e:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                logger.warning(f"Database initialization attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                self.status["last_error"] = f"Database error: {str(e)}"
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to initialize database after {max_retries} attempts: {e}")
                    return False
        
        # Initialize Twitter service
        try:
            twitter_ok = await self.twitter_service.setup(config.twitter)
            self.status["twitter"] = twitter_ok
            if not twitter_ok:
                dev_log("Twitter API initialization failed", "NOTE")
                self.status["last_error"] = "Twitter API initialization failed"
        except Exception as e:
            logger.error(f"Twitter service setup error: {e}")
            self.status["last_error"] = f"Twitter error: {str(e)}"
            self.status["twitter"] = False
        
        # Initialize Telegram service
        try:
            telegram_ok = await self.telegram_service.setup(config.telegram)
            self.status["telegram"] = telegram_ok
            if not telegram_ok:
                dev_log("Telegram bot initialization failed", "NOTE")
                if not self.status["last_error"]:
                    self.status["last_error"] = "Telegram bot initialization failed"
        except Exception as e:
            logger.error(f"Telegram service setup error: {e}")
            if not self.status["last_error"]:
                self.status["last_error"] = f"Telegram error: {str(e)}"
            self.status["telegram"] = False
        
        # We require database and at least one notification service
        self.initialized = self.status["database"] and (self.status["twitter"] or self.status["telegram"])
        
        if self.initialized:
            # Try to send startup notification
            if self.status["telegram"]:
                try:
                    await self.telegram_service.send_system_message(
                        "XCA-Bot started successfully and is ready to monitor Twitter for contract addresses."
                    )
                except Exception as e:
                    logger.warning(f"Failed to send startup notification: {e}")
            
            dev_log("Core monitoring service initialized", "DONE")
        else:
            error_msg = "Failed to initialize monitoring service - "
            if not self.status["database"]:
                error_msg += "database connection failed, "
            if not self.status["twitter"] and not self.status["telegram"]:
                error_msg += "no working notification services"
            logger.error(error_msg)
        
        return self.initialized
    
    async def check_now(self) -> List[TwitterMatch]:
        """Run an immediate check for contract addresses.
        
        Returns:
            List[TwitterMatch]: List of matches found
        """
        if not self.initialized:
            logger.error("Monitor service not initialized")
            return []
        
        if not self.twitter_service.initialized:
            logger.error("Twitter service not initialized")
            return []
        
        dev_log("Running immediate contract address check", "INFO")
        
        matches = await self.twitter_service.check_tweets(
            usernames=self.config.monitoring.usernames,
            regex_patterns=self.config.monitoring.regex_patterns,
            keywords=self.config.monitoring.keywords,
            tweets_per_user=self.config.monitoring.max_tweets_per_check
        )
        
        if matches:
            await self._process_matches(matches)
        
        return matches
    
    async def start_monitoring(self) -> bool:
        """Start continuous monitoring process.
        
        Returns:
            bool: True if monitoring was started successfully
        """
        if self._running:
            logger.warning("Monitoring is already running")
            return True
        
        if not self.initialized:
            logger.error("Monitor service not initialized")
            return False
        
        if not self.twitter_service.initialized:
            logger.error("Twitter service not initialized")
            return False
        
        dev_log("Starting continuous monitoring", "INFO")
        
        # Save monitor state
        await self.db_repo.save_app_state("monitor_running", True)
        await self.db_repo.save_app_state("monitor_start_time", datetime.utcnow().isoformat())
        
        # Start Twitter monitoring
        await self.twitter_service.start_monitoring(
            usernames=self.config.monitoring.usernames,
            regex_patterns=self.config.monitoring.regex_patterns,
            keywords=self.config.monitoring.keywords,
            check_interval_minutes=self.config.monitoring.check_interval_minutes,
            callback=self._process_matches
        )
        
        # Send notification if Telegram is available
        if self.telegram_service.initialized:
            usernames_sample = ", ".join(self.config.monitoring.usernames[:5])
            if len(self.config.monitoring.usernames) > 5:
                usernames_sample += f" and {len(self.config.monitoring.usernames) - 5} more"
                
            await self.telegram_service.send_system_message(
                f"Monitoring started for {len(self.config.monitoring.usernames)} Twitter accounts, "
                f"checking every {self.config.monitoring.check_interval_minutes} minutes. "
                f"Monitoring: {usernames_sample}"
            )
        
        self._running = True
        return True
    
    async def stop_monitoring(self) -> bool:
        """Stop the monitoring process.
        
        Returns:
            bool: True if monitoring was stopped successfully
        """
        if not self._running:
            logger.warning("Monitoring is not running")
            return True
        
        dev_log("Stopping continuous monitoring", "INFO")
        
        # Stop Twitter monitoring
        await self.twitter_service.stop_monitoring()
        
        # Save monitor state
        await self.db_repo.save_app_state("monitor_running", False)
        await self.db_repo.save_app_state("monitor_stop_time", datetime.utcnow().isoformat())
        
        # Send notification if Telegram is available
        if self.telegram_service.initialized:
            await self.telegram_service.send_system_message(
                "Monitoring stopped."
            )
        
        self._running = False
        return True
    
    async def _process_matches(self, matches: List[TwitterMatch]) -> None:
        """Process new matches by storing them and sending notifications.
        
        Args:
            matches: List of Twitter matches containing contract addresses
        """
        if not matches:
            return
        
        dev_log(f"Processing {len(matches)} new matches", "INFO")
        
        # Store matches in database
        for match in matches:
            match_id = await self.db_repo.store_match(match)
            
            # Send to Telegram if available
            if self.telegram_service.initialized:
                results = await self.telegram_service.send_notification(
                    match=match,
                    include_tweet_text=self.config.telegram.include_tweet_text
                )
                
                # Update database with sent status
                for chat_id, success in results.items():
                    if success:
                        await self.db_repo.mark_sent_to_telegram(match_id, chat_id)
            
            # Trigger callbacks
            for callback in self.on_match_callbacks:
                try:
                    await callback(match)
                except Exception as e:
                    logger.error(f"Error in match callback: {e}")
    
    def add_match_listener(self, callback: Callable) -> None:
        """Add a callback to be triggered when new matches are found.
        
        Args:
            callback: Async function that will be called with the match as argument
        """
        self.on_match_callbacks.append(callback)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status.
        
        Returns:
            Dict with status information
        """
        # Get basic status
        status = {
            "initialized": self.initialized,
            "running": self._running,
            "twitter_api_ok": self.twitter_service.initialized if self.twitter_service else False,
            "telegram_bot_ok": self.telegram_service.initialized if self.telegram_service else False,
            "monitoring": {
                "usernames_count": len(self.config.monitoring.usernames) if self.config else 0,
                "regex_patterns_count": len(self.config.monitoring.regex_patterns) if self.config else 0,
                "keywords_count": len(self.config.monitoring.keywords) if self.config else 0,
                "check_interval_minutes": self.config.monitoring.check_interval_minutes if self.config else 0
            }
        }
        
        # Get statistics from database
        try:
            # Get match stats
            match_stats = await self.db_repo.get_match_stats()
            status["matches"] = match_stats
            
            # Get runtime info
            running = await self.db_repo.get_app_state("monitor_running", False)
            start_time = await self.db_repo.get_app_state("monitor_start_time")
            
            if start_time:
                status["start_time"] = start_time
                
                # Calculate uptime if running
                if running:
                    try:
                        start = datetime.fromisoformat(start_time)
                        now = datetime.utcnow()
                        uptime_seconds = (now - start).total_seconds()
                        
                        # Format uptime
                        days, remainder = divmod(uptime_seconds, 86400)
                        hours, remainder = divmod(remainder, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        
                        uptime_str = ""
                        if days > 0:
                            uptime_str += f"{int(days)}d "
                        if hours > 0 or days > 0:
                            uptime_str += f"{int(hours)}h "
                        if minutes > 0 or hours > 0 or days > 0:
                            uptime_str += f"{int(minutes)}m "
                        uptime_str += f"{int(seconds)}s"
                        
                        status["uptime"] = uptime_str
                        status["uptime_seconds"] = uptime_seconds
                    except:
                        pass
        except Exception as e:
            logger.error(f"Error getting monitor status: {e}")
        
        return status 