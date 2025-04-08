"""
XCA-Bot Match Models

This module defines models for Twitter matches containing cryptocurrency contract addresses.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class TwitterMatch(BaseModel):
    """Model representing a match for a cryptocurrency contract address in a tweet."""
    
    # Database fields
    id: Optional[int] = Field(None, description="Database ID")
    
    # Tweet information
    username: str = Field(..., description="Twitter username")
    tweet_id: str = Field(..., description="Tweet ID")
    tweet_text: str = Field(..., description="Full tweet text")
    matched_patterns: List[str] = Field(..., description="Patterns that matched this tweet")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp when the match was found")
    
    # Extracted data
    contract_addresses: List[str] = Field(default_factory=list, description="Contract addresses found in the tweet")
    
    # URLs and references
    tweet_url: str = Field(..., description="URL to the tweet")
    
    # Processing status
    sent_to_telegram: bool = Field(False, description="Whether this match was sent to Telegram")
    destinations_sent: List[str] = Field(default_factory=list, description="Telegram destinations this match was sent to")
    
    @validator('tweet_url')
    def validate_tweet_url(cls, v, values):
        """Validate or generate tweet URL if needed."""
        if not v and 'username' in values and 'tweet_id' in values:
            return f"https://twitter.com/{values['username']}/status/{values['tweet_id']}"
        return v
    
    def to_message(self, include_tweet_text: bool = True) -> str:
        """Convert the match to a formatted message for Telegram."""
        message_parts = []
        
        # Username
        message_parts.append(f"Username: @{self.username}")
        
        # Contract addresses
        if self.contract_addresses:
            message_parts.append(f"Contract: {', '.join(self.contract_addresses)}")
        else:
            message_parts.append("No CA found")
        
        # Tweet text (optional)
        if include_tweet_text and self.tweet_text:
            # Limit tweet text to a reasonable length
            max_text_length = 200
            tweet_summary = self.tweet_text
            if len(tweet_summary) > max_text_length:
                tweet_summary = tweet_summary[:max_text_length] + "..."
            message_parts.append(f"Tweet: {tweet_summary}")
        
        # Tweet URL
        message_parts.append(f"Link: {self.tweet_url}")
        
        # Timestamp
        formatted_timestamp = self.timestamp.strftime("%Y-%m-%d %H:%M UTC")
        message_parts.append(f"Time: {formatted_timestamp}")
        
        return "\n".join(message_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the match to a dictionary for API responses."""
        return {
            "id": self.id,
            "username": self.username,
            "tweet_id": self.tweet_id,
            "tweet_text": self.tweet_text,
            "matched_patterns": self.matched_patterns,
            "contract_addresses": self.contract_addresses,
            "timestamp": self.timestamp.isoformat(),
            "tweet_url": self.tweet_url,
            "sent_to_telegram": self.sent_to_telegram,
            "destinations_sent": self.destinations_sent
        } 