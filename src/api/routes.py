"""
XCA-Bot API Routes

This module defines the FastAPI routes for the XCA-Bot API.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from src.core.logger import logger, dev_log
from src.core.monitor import MonitorService
from src.models.config import AppConfig, TelegramDestination
from src.models.match import TwitterMatch

# Create API router
router = APIRouter()

# Models for API requests and responses
class StatusResponse(BaseModel):
    """Response model for status endpoint."""
    initialized: bool
    running: bool
    twitter_api_ok: bool
    telegram_bot_ok: bool
    monitoring: Dict[str, Any]
    matches: Optional[Dict[str, int]] = None
    uptime: Optional[str] = None

class MatchResponse(BaseModel):
    """Response model for matches endpoint."""
    id: Optional[int] = None
    username: str
    tweet_id: str
    tweet_text: str
    matched_patterns: List[str]
    contract_addresses: List[str]
    timestamp: str
    tweet_url: str

class TelegramDestinationRequest(BaseModel):
    """Request model for adding Telegram destinations."""
    chat_id: str
    description: Optional[str] = None

class TelegramTestResponse(BaseModel):
    """Response model for testing Telegram destinations."""
    success: bool
    message: str

class CheckRequest(BaseModel):
    """Request model for checking specific usernames."""
    usernames: List[str]

class SimpleResponse(BaseModel):
    """Simple response model with success status and message."""
    success: bool
    message: str

# Dependency for accessing the monitor service
def get_monitor_service():
    """Provides the monitor service instance."""
    # In a real application, this would be retrieved from a global state
    # or dependency injection system. For simplicity, we'll assume it's
    # initialized elsewhere and available here.
    from main import monitor_service
    return monitor_service


@router.get("/status", response_model=StatusResponse)
async def get_status(monitor: MonitorService = Depends(get_monitor_service)):
    """Get the current status of the monitor."""
    status = await monitor.get_status()
    return StatusResponse(**status)


@router.post("/start", response_model=SimpleResponse)
async def start_monitoring(
    background_tasks: BackgroundTasks,
    monitor: MonitorService = Depends(get_monitor_service)
):
    """Start the monitoring process."""
    if not monitor.initialized:
        raise HTTPException(status_code=400, detail="Monitor not initialized")
    
    dev_log("API request: Start monitoring", "INFO")
    
    # Start monitoring in the background
    background_tasks.add_task(monitor.start_monitoring)
    
    return SimpleResponse(
        success=True,
        message="Monitoring process started"
    )


@router.post("/stop", response_model=SimpleResponse)
async def stop_monitoring(
    background_tasks: BackgroundTasks,
    monitor: MonitorService = Depends(get_monitor_service)
):
    """Stop the monitoring process."""
    if not monitor.initialized:
        raise HTTPException(status_code=400, detail="Monitor not initialized")
    
    dev_log("API request: Stop monitoring", "INFO")
    
    # Stop monitoring in the background
    background_tasks.add_task(monitor.stop_monitoring)
    
    return SimpleResponse(
        success=True,
        message="Monitoring process stopped"
    )


@router.post("/check", response_model=List[MatchResponse])
async def check_now(
    request: Optional[CheckRequest] = None,
    monitor: MonitorService = Depends(get_monitor_service)
):
    """Run an immediate check for contract addresses."""
    if not monitor.initialized:
        raise HTTPException(status_code=400, detail="Monitor not initialized")
    
    if not monitor.twitter_service.initialized:
        raise HTTPException(status_code=400, detail="Twitter API not configured")
    
    dev_log("API request: Check now", "INFO")
    
    # Use provided usernames or default to configured ones
    usernames = request.usernames if request and request.usernames else monitor.config.monitoring.usernames
    
    if not usernames:
        raise HTTPException(status_code=400, detail="No usernames configured or provided")
    
    # Get configured patterns and keywords
    patterns = monitor.config.monitoring.regex_patterns
    keywords = monitor.config.monitoring.keywords
    
    # Run check
    matches = await monitor.twitter_service.check_tweets(
        usernames=usernames,
        regex_patterns=patterns,
        keywords=keywords
    )
    
    # Process matches if any found
    if matches:
        await monitor._process_matches(matches)
    
    # Convert matches to response model
    return [
        MatchResponse(
            id=match.id,
            username=match.username,
            tweet_id=match.tweet_id,
            tweet_text=match.tweet_text,
            matched_patterns=match.matched_patterns,
            contract_addresses=match.contract_addresses,
            timestamp=match.timestamp.isoformat(),
            tweet_url=match.tweet_url
        )
        for match in matches
    ]


@router.get("/matches", response_model=List[MatchResponse])
async def get_recent_matches(
    limit: int = 10,
    monitor: MonitorService = Depends(get_monitor_service)
):
    """Get recent matches from the database."""
    if not monitor.initialized:
        raise HTTPException(status_code=400, detail="Monitor not initialized")
    
    matches = await monitor.db_repo.get_recent_matches(limit=limit)
    
    # Convert to response model
    return [
        MatchResponse(
            id=match.id,
            username=match.username,
            tweet_id=match.tweet_id,
            tweet_text=match.tweet_text,
            matched_patterns=match.matched_patterns,
            contract_addresses=match.contract_addresses,
            timestamp=match.timestamp.isoformat(),
            tweet_url=match.tweet_url
        )
        for match in matches
    ]


@router.get("/config", response_model=Dict[str, Any])
async def get_config(monitor: MonitorService = Depends(get_monitor_service)):
    """Get the current configuration (with sensitive data masked)."""
    if not monitor.initialized:
        raise HTTPException(status_code=400, detail="Monitor not initialized")
    
    return monitor.config.to_dict()


@router.post("/config/telegram/destinations", response_model=SimpleResponse)
async def add_telegram_destination(
    destination: TelegramDestinationRequest,
    monitor: MonitorService = Depends(get_monitor_service)
):
    """Add a new Telegram destination for forwarding."""
    if not monitor.initialized:
        raise HTTPException(status_code=400, detail="Monitor not initialized")
    
    if not monitor.telegram_service.initialized:
        raise HTTPException(status_code=400, detail="Telegram service not initialized")
    
    # Create new destination
    new_dest = TelegramDestination(
        chat_id=destination.chat_id,
        description=destination.description
    )
    
    # Check if already exists
    for dest in monitor.config.telegram.forwarding_destinations:
        if dest.chat_id == new_dest.chat_id:
            return SimpleResponse(
                success=False,
                message="Destination already exists"
            )
    
    # Add to config
    monitor.config.telegram.forwarding_destinations.append(new_dest)
    
    dev_log(f"Added Telegram forwarding destination: {new_dest.chat_id}", "INFO")
    
    return SimpleResponse(
        success=True,
        message=f"Added Telegram destination: {new_dest.chat_id}"
    )


@router.delete("/config/telegram/destinations/{chat_id}", response_model=SimpleResponse)
async def remove_telegram_destination(
    chat_id: str,
    monitor: MonitorService = Depends(get_monitor_service)
):
    """Remove a Telegram destination."""
    if not monitor.initialized:
        raise HTTPException(status_code=400, detail="Monitor not initialized")
    
    # Check if exists and remove
    original_count = len(monitor.config.telegram.forwarding_destinations)
    monitor.config.telegram.forwarding_destinations = [
        dest for dest in monitor.config.telegram.forwarding_destinations
        if dest.chat_id != chat_id
    ]
    
    if len(monitor.config.telegram.forwarding_destinations) < original_count:
        dev_log(f"Removed Telegram forwarding destination: {chat_id}", "INFO")
        return SimpleResponse(
            success=True,
            message=f"Removed Telegram destination: {chat_id}"
        )
    else:
        return SimpleResponse(
            success=False,
            message=f"Destination {chat_id} not found"
        )


@router.post("/config/telegram/test/{chat_id}", response_model=TelegramTestResponse)
async def test_telegram_destination(
    chat_id: str,
    monitor: MonitorService = Depends(get_monitor_service)
):
    """Test sending a message to a Telegram destination."""
    if not monitor.initialized:
        raise HTTPException(status_code=400, detail="Monitor not initialized")
    
    if not monitor.telegram_service.initialized:
        raise HTTPException(status_code=400, detail="Telegram service not initialized")
    
    # Attempt to send test message
    result = await monitor.telegram_service.test_destination(chat_id)
    
    if result:
        return TelegramTestResponse(
            success=True,
            message=f"Successfully sent test message to {chat_id}"
        )
    else:
        return TelegramTestResponse(
            success=False,
            message=f"Failed to send test message to {chat_id}"
        ) 