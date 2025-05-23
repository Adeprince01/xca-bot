"""
XCA-Bot API Routes

This module defines the FastAPI routes for the XCA-Bot API.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Body
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
    error: Optional[str] = None

# Dependency for accessing the monitor service
def get_monitor_service():
    """Provides the monitor service instance."""
    from src.api.server import get_monitor_service as get_global_monitor
    monitor = get_global_monitor()
    if not monitor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Service unavailable. Monitor not initialized."
        )
    return monitor


# Enhanced dependency that checks if the monitor is properly initialized
def require_initialized_monitor():
    """Requires the monitor service to be fully initialized."""
    monitor = get_monitor_service()
    if not monitor.initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Monitor service is not initialized. Please check configuration."
        )
    return monitor


# Dependency for Twitter service
def require_twitter_service():
    """Requires the Twitter service to be initialized."""
    monitor = require_initialized_monitor()
    if not hasattr(monitor, "twitter_service") or not monitor.twitter_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Twitter service is not available."
        )
    if not monitor.twitter_service.initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Twitter service is not initialized. Please check API credentials."
        )
    return monitor


# Dependency for Telegram service
def require_telegram_service():
    """Requires the Telegram service to be initialized."""
    monitor = require_initialized_monitor()
    if not hasattr(monitor, "telegram_service") or not monitor.telegram_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram service is not available."
        )
    if not monitor.telegram_service.initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram service is not initialized. Please check bot token."
        )
    return monitor


@router.get("/status", response_model=StatusResponse)
async def get_status(monitor: MonitorService = Depends(get_monitor_service)):
    """Get the current status of the monitor."""
    try:
        status = await monitor.get_status()
        return StatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting monitor status: {str(e)}"
        )


@router.post("/monitoring/start", response_model=SimpleResponse)
async def start_monitoring(
    background_tasks: BackgroundTasks,
    monitor: MonitorService = Depends(require_initialized_monitor)
):
    """Start the monitoring process."""
    dev_log("API request: Start monitoring", "INFO")
    
    try:
        # Start monitoring in the background
        background_tasks.add_task(monitor.start_monitoring)
        
        return SimpleResponse(
            success=True,
            message="Monitoring process started"
        )
    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}", exc_info=True)
        return SimpleResponse(
            success=False,
            message="Failed to start monitoring",
            error=str(e)
        )


@router.post("/monitoring/stop", response_model=SimpleResponse)
async def stop_monitoring(
    background_tasks: BackgroundTasks,
    monitor: MonitorService = Depends(require_initialized_monitor)
):
    """Stop the monitoring process."""
    dev_log("API request: Stop monitoring", "INFO")
    
    try:
        # Stop monitoring in the background
        background_tasks.add_task(monitor.stop_monitoring)
        
        return SimpleResponse(
            success=True,
            message="Monitoring process stopped"
        )
    except Exception as e:
        logger.error(f"Error stopping monitoring: {str(e)}", exc_info=True)
        return SimpleResponse(
            success=False,
            message="Failed to stop monitoring",
            error=str(e)
        )


@router.post("/check", response_model=List[MatchResponse])
async def check_now(
    request: Optional[CheckRequest] = None,
    monitor: MonitorService = Depends(require_twitter_service)
):
    """Run an immediate check for contract addresses."""
    dev_log("API request: Check now", "INFO")
    
    # Use provided usernames or default to configured ones
    usernames = request.usernames if request and request.usernames else monitor.config.monitoring.usernames
    
    if not usernames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No usernames configured or provided"
        )
    
    try:
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
    except Exception as e:
        logger.error(f"Error checking tweets: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking tweets: {str(e)}"
        )


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


@router.put("/config", response_model=Dict[str, Any])
async def update_config(
    config_update: Dict[str, Any] = Body(...),
    monitor: MonitorService = Depends(get_monitor_service)
):
    """Update the application configuration."""
    if not monitor.initialized:
        raise HTTPException(status_code=400, detail="Monitor not initialized")
    try:
        # Create a new AppConfig from the provided update
        new_config = AppConfig.from_dict(config_update)
        monitor.config = new_config
        dev_log("Configuration updated via API", "INFO")
        return monitor.config.to_dict()
    except Exception as e:
        logger.error(f"Failed to update config: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Failed to update config: {e}") 