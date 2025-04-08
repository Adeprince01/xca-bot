"""
XCA-Bot Database Models

This module defines SQLAlchemy ORM models for database persistence.
"""

from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

Base = declarative_base()


class Match(Base):
    """Database model for storing Twitter matches."""
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, index=True)
    tweet_id = Column(String(50), nullable=False, unique=True)
    tweet_text = Column(Text, nullable=False)
    matched_patterns = Column(Text, nullable=False)  # Stored as JSON string
    contract_addresses = Column(Text, nullable=True)  # Stored as JSON string
    timestamp = Column(DateTime, default=datetime.utcnow)
    tweet_url = Column(String(255), nullable=False)
    sent_to_telegram = Column(Boolean, default=False)
    destinations_sent = Column(Text, nullable=True)  # Stored as JSON string
    
    def to_dict(self):
        """Convert database model to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "tweet_id": self.tweet_id,
            "tweet_text": self.tweet_text,
            "matched_patterns": json.loads(self.matched_patterns),
            "contract_addresses": json.loads(self.contract_addresses) if self.contract_addresses else [],
            "timestamp": self.timestamp.isoformat(),
            "tweet_url": self.tweet_url,
            "sent_to_telegram": self.sent_to_telegram,
            "destinations_sent": json.loads(self.destinations_sent) if self.destinations_sent else []
        }
    
    @classmethod
    def from_twitter_match(cls, twitter_match):
        """Create a database model from a TwitterMatch Pydantic model."""
        return cls(
            username=twitter_match.username,
            tweet_id=twitter_match.tweet_id,
            tweet_text=twitter_match.tweet_text,
            matched_patterns=json.dumps(twitter_match.matched_patterns),
            contract_addresses=json.dumps(twitter_match.contract_addresses),
            timestamp=twitter_match.timestamp,
            tweet_url=twitter_match.tweet_url,
            sent_to_telegram=twitter_match.sent_to_telegram,
            destinations_sent=json.dumps(twitter_match.destinations_sent)
        )


class AppState(Base):
    """Database model for storing application state."""
    __tablename__ = "app_state"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_engine(db_url="sqlite:///xca-bot.db"):
    """Create a SQLAlchemy engine."""
    return create_engine(
        db_url,
        connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {},
        poolclass=StaticPool
    )


def get_session_maker(engine):
    """Create a sessionmaker for the given engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(db_url="sqlite:///xca-bot.db"):
    """Initialize database and create tables."""
    engine = get_engine(db_url)
    Base.metadata.create_all(bind=engine)
    return engine 