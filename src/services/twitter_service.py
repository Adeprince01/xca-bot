"""
XCA-Bot Twitter Service

This module provides functionality for monitoring Twitter and extracting contract addresses.
"""

import re
import asyncio
from typing import List, Dict, Any, Optional, Set
import tweepy
from datetime import datetime, timedelta

from src.core.logger import logger, dev_log
from src.models.config import TwitterConfig
from src.models.match import TwitterMatch


class TwitterService:
    """Service for interacting with Twitter API and monitoring tweets."""
    
    def __init__(self):
        """Initialize Twitter service."""
        self.client = None
        self.api = None
        self.initialized = False
        self._task = None
        self._running = False
    
    async def setup(self, config: TwitterConfig) -> bool:
        """Set up Twitter API client."""
        try:
            # Validate configuration
            if not all([
                config.api_key, 
                config.api_secret, 
                config.access_token,
                config.access_token_secret
            ]):
                logger.error("Twitter API configuration is incomplete")
                return False
            
            # Initialize API client
            auth = tweepy.OAuth1UserHandler(
                config.api_key,
                config.api_secret,
                config.access_token,
                config.access_token_secret
            )
            
            # Create API client (v1.1)
            self.api = tweepy.API(auth)
            
            # Verify credentials
            user = await asyncio.to_thread(self.api.verify_credentials)
            logger.info(f"Twitter API initialized successfully as @{user.screen_name}")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Twitter API: {e}")
            self.initialized = False
            return False
    
    async def check_tweets(
        self, 
        usernames: List[str], 
        regex_patterns: List[str], 
        keywords: List[str], 
        tweets_per_user: int = 10
    ) -> List[TwitterMatch]:
        """Check tweets from monitored users for cryptocurrency contracts.
        
        Args:
            usernames: List of Twitter usernames to check
            regex_patterns: List of regex patterns to match in tweets
            keywords: List of keywords to match in tweets
            tweets_per_user: Number of tweets to fetch per user
            
        Returns:
            List of TwitterMatch objects for matches found
        """
        if not self.initialized or not self.api:
            logger.error("Twitter API not initialized")
            return []
        
        if not usernames:
            logger.warning("No usernames provided for monitoring")
            return []
        
        logger.info(f"Checking tweets for {len(usernames)} users")
        dev_log(f"Checking Twitter for: {', '.join(usernames[:5])}{' and others' if len(usernames) > 5 else ''}", "INFO")
        
        # Compile regex patterns
        compiled_patterns = []
        for pattern in regex_patterns:
            try:
                compiled_patterns.append((pattern, re.compile(pattern, re.IGNORECASE)))
            except re.error as e:
                logger.error(f"Invalid regex pattern '{pattern}': {e}")
        
        # Prepare keywords
        keywords_lower = [kw.lower() for kw in keywords]
        
        matches = []
        
        # Check each user's timeline
        for username in usernames:
            try:
                # Remove @ if present
                clean_username = username.replace('@', '')
                
                # Get user's recent tweets
                try:
                    tweets = await asyncio.to_thread(
                        self.api.user_timeline,
                        screen_name=clean_username,
                        count=tweets_per_user,
                        tweet_mode="extended",
                        include_rts=False  # Exclude retweets
                    )
                except tweepy.NotFound:
                    logger.warning(f"User not found: @{clean_username}")
                    continue
                except tweepy.Unauthorized:
                    logger.warning(f"Not authorized to view tweets from @{clean_username}")
                    continue
                except Exception as e:
                    logger.error(f"Error fetching tweets for @{clean_username}: {e}")
                    continue
                
                # Process each tweet
                for tweet in tweets:
                    tweet_id = tweet.id_str
                    tweet_text = tweet.full_text
                    
                    # Check for matches
                    matched_patterns = []
                    matched_contract_addresses = []
                    
                    # Check regex patterns for contract addresses
                    for pattern_str, pattern in compiled_patterns:
                        # For contract addresses, we not only need to know it matched,
                        # but also extract all the actual addresses
                        if pattern_str == "0x[a-fA-F0-9]{40}":  # Ethereum address pattern
                            addresses = pattern.findall(tweet_text)
                            if addresses:
                                matched_patterns.append(pattern_str)
                                matched_contract_addresses.extend(addresses)
                        elif pattern_str == "$[A-Za-z][A-Za-z0-9]+":  # Ticker symbol pattern
                            tickers = pattern.findall(tweet_text)
                            if tickers:
                                matched_patterns.append(pattern_str)
                                matched_contract_addresses.extend(tickers)
                        elif pattern.search(tweet_text):
                            matched_patterns.append(pattern_str)
                    
                    # Check keywords
                    tweet_text_lower = tweet_text.lower()
                    for keyword in keywords_lower:
                        if keyword in tweet_text_lower:
                            matched_patterns.append(keyword)
                    
                    # If we have matches, create a TwitterMatch object
                    if matched_patterns:
                        logger.info(f"Found match in @{clean_username} tweet")
                        
                        # Create TwitterMatch
                        match = TwitterMatch(
                            username=clean_username,
                            tweet_id=tweet_id,
                            tweet_text=tweet_text,
                            matched_patterns=matched_patterns,
                            contract_addresses=matched_contract_addresses,
                            tweet_url=f"https://twitter.com/{clean_username}/status/{tweet_id}",
                            timestamp=datetime.utcnow(),
                            sent_to_telegram=False,
                            destinations_sent=[]
                        )
                        
                        matches.append(match)
                
                # Respect rate limits with a small delay
                await asyncio.sleep(0.2)
                
            except tweepy.TooManyRequests:
                logger.error("Twitter API rate limit exceeded")
                # Wait before continuing
                await asyncio.sleep(60)
                break
            except Exception as e:
                logger.error(f"Error processing tweets for {username}: {e}")
        
        logger.info(f"Found {len(matches)} matching tweets")
        return matches
    
    async def start_monitoring(
        self,
        usernames: List[str],
        regex_patterns: List[str],
        keywords: List[str],
        check_interval_minutes: int,
        callback
    ):
        """Start continuous monitoring for contract addresses.
        
        Args:
            usernames: List of Twitter usernames to monitor
            regex_patterns: List of regex patterns to match
            keywords: List of keywords to match
            check_interval_minutes: Time between checks in minutes
            callback: Async function to call with matches
        """
        if self._running:
            logger.warning("Monitoring is already running")
            return
        
        if not self.initialized:
            logger.error("Twitter API not initialized")
            return
        
        self._running = True
        dev_log("Starting Twitter monitoring task", "INFO")
        
        async def monitoring_task():
            while self._running:
                try:
                    # Check tweets
                    matches = await self.check_tweets(
                        usernames,
                        regex_patterns,
                        keywords
                    )
                    
                    # Call callback with any matches found
                    if matches:
                        await callback(matches)
                    
                    # Wait for next check
                    logger.info(f"Next check in {check_interval_minutes} minutes")
                    for _ in range(check_interval_minutes * 60):
                        if not self._running:
                            break
                        await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error in monitoring task: {e}")
                    await asyncio.sleep(60)  # Wait before retrying
        
        # Start task
        self._task = asyncio.create_task(monitoring_task())
        logger.info(f"Monitoring started for {len(usernames)} users")
    
    async def stop_monitoring(self):
        """Stop monitoring task."""
        if not self._running:
            logger.warning("Monitoring is not running")
            return
        
        self._running = False
        if self._task:
            dev_log("Stopping Twitter monitoring task", "INFO")
            # Wait for task to finish
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Monitoring task did not stop gracefully, cancelling")
                self._task.cancel()
            
            self._task = None
        
        logger.info("Monitoring stopped") 