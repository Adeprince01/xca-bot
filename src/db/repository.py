"""
XCA-Bot Database Repository

This module provides an asynchronous interface to the database.
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import update, delete, desc, func
from contextlib import asynccontextmanager

from src.core.logger import logger
from src.models.match import TwitterMatch
from src.db.models import Match, AppState, Base


class DatabaseRepository:
    """Async database repository for XCA-Bot."""
    
    def __init__(self, db_url: str = "sqlite+aiosqlite:///xca-bot.db"):
        """Initialize database repository with async engine."""
        self.engine = create_async_engine(
            db_url,
            echo=False,
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
        )
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        
    async def init_db(self):
        """Initialize database and create tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    
    @asynccontextmanager
    async def get_session(self):
        """Provide an async session context."""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database error: {e}")
                raise
    
    async def store_match(self, match: TwitterMatch) -> int:
        """Store a TwitterMatch in the database."""
        db_match = Match.from_twitter_match(match)
        
        async with self.get_session() as session:
            # Check if tweet_id already exists
            result = await session.execute(
                select(Match).where(Match.tweet_id == db_match.tweet_id)
            )
            existing = result.scalars().first()
            
            if existing:
                # Update existing record
                existing.matched_patterns = db_match.matched_patterns
                existing.contract_addresses = db_match.contract_addresses
                existing.sent_to_telegram = db_match.sent_to_telegram
                existing.destinations_sent = db_match.destinations_sent
                await session.commit()
                return existing.id
            else:
                # Insert new record
                session.add(db_match)
                await session.commit()
                await session.refresh(db_match)
                return db_match.id
    
    async def get_recent_matches(self, limit: int = 10) -> List[TwitterMatch]:
        """Get recent matches from database."""
        async with self.get_session() as session:
            result = await session.execute(
                select(Match).order_by(desc(Match.timestamp)).limit(limit)
            )
            
            matches = []
            for db_match in result.scalars().all():
                match_dict = db_match.to_dict()
                matches.append(TwitterMatch(**match_dict))
            
            return matches
    
    async def get_matches_by_usernames(self, usernames: List[str], limit: int = 50) -> List[TwitterMatch]:
        """Get matches for specific usernames."""
        async with self.get_session() as session:
            result = await session.execute(
                select(Match)
                .where(Match.username.in_([u.replace('@', '') for u in usernames]))
                .order_by(desc(Match.timestamp))
                .limit(limit)
            )
            
            matches = []
            for db_match in result.scalars().all():
                match_dict = db_match.to_dict()
                matches.append(TwitterMatch(**match_dict))
            
            return matches
    
    async def mark_sent_to_telegram(self, match_id: int, destination: str) -> bool:
        """Mark a match as sent to a specific Telegram destination."""
        async with self.get_session() as session:
            result = await session.execute(
                select(Match).where(Match.id == match_id)
            )
            db_match = result.scalars().first()
            
            if not db_match:
                return False
            
            # Update destinations list
            destinations = json.loads(db_match.destinations_sent) if db_match.destinations_sent else []
            if destination not in destinations:
                destinations.append(destination)
            
            db_match.sent_to_telegram = True
            db_match.destinations_sent = json.dumps(destinations)
            await session.commit()
            return True
    
    async def get_match_stats(self) -> Dict[str, Any]:
        """Get statistics about matches."""
        async with self.get_session() as session:
            # Total matches
            result = await session.execute(select(func.count()).select_from(Match))
            total_matches = result.scalar() or 0
            
            # Matches today
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            result = await session.execute(
                select(func.count()).select_from(Match).where(Match.timestamp >= today)
            )
            matches_today = result.scalar() or 0
            
            # Matches in the last 7 days
            week_ago = datetime.utcnow() - timedelta(days=7)
            result = await session.execute(
                select(func.count()).select_from(Match).where(Match.timestamp >= week_ago)
            )
            matches_week = result.scalar() or 0
            
            # Unique usernames with matches
            result = await session.execute(
                select(func.count(Match.username.distinct())).select_from(Match)
            )
            unique_usernames = result.scalar() or 0
            
            return {
                "total": total_matches,
                "today": matches_today,
                "last_7_days": matches_week,
                "unique_usernames": unique_usernames
            }
    
    async def save_app_state(self, key: str, value: Any) -> None:
        """Save application state."""
        async with self.get_session() as session:
            # Check if key already exists
            result = await session.execute(
                select(AppState).where(AppState.key == key)
            )
            state = result.scalars().first()
            
            value_str = json.dumps(value) if value is not None else None
            
            if state:
                # Update existing state
                state.value = value_str
                state.updated_at = datetime.utcnow()
            else:
                # Create new state
                new_state = AppState(key=key, value=value_str)
                session.add(new_state)
            
            await session.commit()
    
    async def get_app_state(self, key: str, default: Any = None) -> Any:
        """Get application state."""
        async with self.get_session() as session:
            result = await session.execute(
                select(AppState).where(AppState.key == key)
            )
            state = result.scalars().first()
            
            if not state or not state.value:
                return default
            
            try:
                return json.loads(state.value)
            except:
                return state.value 