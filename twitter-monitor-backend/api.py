#!/usr/bin/env python3
import os
import json
import asyncio
import logging
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from twitter_monitor import TwitterMonitor
from collections import deque
import aiofiles
import aiofiles.os

# Configure logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO,
    filename='twitter_monitor.log'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Twitter Monitor API",
    description="API for monitoring Twitter/X for specific content",
    version="1.0.0"
)

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Twitter Monitor
monitor = TwitterMonitor()

# Initialize APScheduler
scheduler = AsyncIOScheduler(
    jobstores={'default': MemoryJobStore()},
    timezone=timezone.utc
)

# Job ID for the monitoring task
MONITOR_JOB_ID = 'twitter_monitor'

# Create an in-memory buffer for recent logs
log_buffer = deque(maxlen=1000)  # Keep last 1000 log entries

class LogHandler(logging.Handler):
    def emit(self, record):
        try:
            log_entry = self.format(record)
            log_buffer.append(log_entry)
        except Exception:
            self.handleError(record)

# Add our custom handler to the logger
log_handler = LogHandler()
log_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(log_handler)

# Event queues for SSE
status_updates = asyncio.Queue()
match_updates = asyncio.Queue()

# Start scheduler on app startup
@app.on_event("startup")
async def startup_event():
    scheduler.start()

# Shutdown scheduler on app shutdown
@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

# Pydantic models for request/response validation
class TwitterConfig(BaseModel):
    api_key: str = Field(..., description="Twitter API Key")
    api_secret: str = Field(..., description="Twitter API Secret")
    access_token: str = Field(..., description="Twitter Access Token")
    access_token_secret: str = Field(..., description="Twitter Access Token Secret")

class TelegramConfig(BaseModel):
    bot_token: str = Field(..., description="Telegram Bot Token")
    channel_id: str = Field(..., description="Telegram Channel ID")
    enable_direct_messages: bool = Field(True, description="Enable direct messages to bot")
    include_tweet_text: bool = Field(True, description="Include tweet text in notifications")

class MonitoringConfig(BaseModel):
    check_interval_minutes: int = Field(15, description="Check interval in minutes", ge=1, le=60)
    usernames: List[str] = Field([], description="Twitter usernames to monitor")
    regex_patterns: List[str] = Field([], description="Regex patterns to match")
    keywords: List[str] = Field([], description="Keywords to match")

class FullConfig(BaseModel):
    twitter: TwitterConfig
    telegram: TelegramConfig
    monitoring: MonitoringConfig

class StatusResponse(BaseModel):
    is_running: bool
    pid: Optional[int] = None
    uptime: Optional[str] = None
    monitored_users: int
    regex_patterns: int
    keywords: int
    check_interval: int
    last_check: Optional[str] = None

class Match(BaseModel):
    username: str
    tweet_id: str
    tweet_text: str
    matched_pattern: List[str]
    timestamp: str
    tweet_url: str

class MatchesResponse(BaseModel):
    matches: List[Match]
    total: int

class MessageResponse(BaseModel):
    message: str
    success: bool

async def monitor_job():
    """The monitoring job that will be scheduled."""
    try:
        logger.info("Running scheduled check")
        matches = await monitor.check_tweets()
        logger.info("Scheduled check completed")
        
        # Push any new matches to the match_updates queue
        if matches:
            for match in matches:
                await match_updates.put(match)
                logger.info(f"New match found: {match['username']} - {match['tweet_id']}")
    except Exception as e:
        logger.error(f"Error in monitoring job: {str(e)}")
        raise

def get_job_status():
    """Get the current status of the monitoring job."""
    job = scheduler.get_job(MONITOR_JOB_ID)
    if not job:
        return False, None, None
    
    # Calculate uptime if job is running
    start_time = job.next_run_time
    if start_time:
        now = datetime.now(timezone.utc)
        uptime = now - start_time
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
    else:
        uptime_str = None
    
    return True, job.next_run_time, uptime_str

# API Routes
@app.get("/", response_model=MessageResponse)
async def root():
    """Root endpoint to check if API is running."""
    return {"message": "Twitter Monitor API is running", "success": True}

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get the current status of the monitor."""
    is_running, next_run, uptime = get_job_status()
    
    # Get config info
    usernames = monitor.config["monitoring"]["usernames"]
    patterns = monitor.config["monitoring"]["regex_patterns"]
    keywords = monitor.config["monitoring"]["keywords"]
    interval = monitor.config["monitoring"]["check_interval_minutes"]
    
    # Get last check time from logs if available
    last_check = None
    try:
        with open('twitter_monitor.log', 'r') as f:
            logs = f.readlines()
            for line in reversed(logs):
                if "Running scheduled check" in line:
                    last_check = line.split(']')[0].strip('[')
                    break
    except Exception as e:
        logger.warning(f"Error reading log file: {str(e)}")
    
    return {
        "is_running": is_running,
        "pid": None,  # No longer using PIDs
        "uptime": uptime,
        "monitored_users": len(usernames),
        "regex_patterns": len(patterns),
        "keywords": len(keywords),
        "check_interval": interval,
        "last_check": last_check
    }

@app.post("/start", response_model=MessageResponse)
async def start_monitoring():
    """Start the monitoring process."""
    # Check if already running
    job = scheduler.get_job(MONITOR_JOB_ID)
    if job:
        return {"message": "Monitoring is already running", "success": False}
    
    # Check if configuration is complete
    if (not monitor.config["twitter"]["api_key"] or 
        not monitor.config["telegram"]["bot_token"]):
        raise HTTPException(status_code=400, detail="Configuration incomplete. Please configure API keys first.")
    
    try:
        # Get interval from config
        interval_minutes = monitor.config["monitoring"]["check_interval_minutes"]
        
        # Add the job to the scheduler
        scheduler.add_job(
            monitor_job,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=MONITOR_JOB_ID,
            name='Twitter Monitor',
            replace_existing=True
        )
        
        # Run the job immediately
        await monitor_job()
        
        logger.info("Monitoring started")
        return {"message": "Monitoring started", "success": True}
    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")

@app.post("/stop", response_model=MessageResponse)
async def stop_monitoring():
    """Stop the monitoring process."""
    job = scheduler.get_job(MONITOR_JOB_ID)
    if not job:
        return {"message": "Monitoring is not running", "success": False}
    
    try:
        scheduler.remove_job(MONITOR_JOB_ID)
        logger.info("Monitoring stopped")
        return {"message": "Monitoring stopped", "success": True}
    except Exception as e:
        logger.error(f"Error stopping monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")

@app.get("/config", response_model=FullConfig)
async def get_config():
    """Get the current configuration."""
    return monitor.config

@app.post("/config", response_model=MessageResponse)
async def update_config(config: FullConfig):
    """Update the configuration."""
    try:
        # Update config
        monitor.config["twitter"] = config.twitter.dict()
        monitor.config["telegram"] = config.telegram.dict()
        monitor.config["monitoring"] = config.monitoring.dict()
        
        # Save config
        monitor.save_config()
        
        # Reinitialize monitor with new config
        monitor.setup_twitter_api()
        monitor.setup_telegram_bot()
        
        return {"message": "Configuration updated successfully", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating configuration: {str(e)}")

@app.get("/matches", response_model=MatchesResponse)
async def get_matches(limit: int = 10):
    """Get recent matches."""
    try:
        matches = monitor.get_recent_matches(limit)
        return {"matches": matches, "total": len(matches)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting matches: {str(e)}")

@app.get("/users", response_model=List[str])
async def get_users():
    """Get the list of monitored users."""
    return monitor.config["monitoring"]["usernames"]

@app.post("/users", response_model=MessageResponse)
async def update_users(usernames: List[str]):
    """Update the list of monitored users."""
    try:
        monitor.update_usernames(usernames)
        return {"message": f"Updated usernames list: {len(usernames)} users", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating users: {str(e)}")

@app.get("/patterns", response_model=List[str])
async def get_patterns():
    """Get the list of regex patterns."""
    return monitor.config["monitoring"]["regex_patterns"]

@app.post("/patterns", response_model=MessageResponse)
async def update_patterns(patterns: List[str]):
    """Update the list of regex patterns."""
    try:
        monitor.update_patterns(patterns)
        return {"message": f"Updated regex patterns: {len(patterns)} patterns", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating patterns: {str(e)}")

@app.get("/keywords", response_model=List[str])
async def get_keywords():
    """Get the list of keywords."""
    return monitor.config["monitoring"]["keywords"]

@app.post("/keywords", response_model=MessageResponse)
async def update_keywords(keywords: List[str]):
    """Update the list of keywords."""
    try:
        monitor.update_keywords(keywords)
        return {"message": f"Updated keywords: {len(keywords)} keywords", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating keywords: {str(e)}")

@app.post("/export", response_model=MessageResponse)
async def export_matches(filename: str = "matches_export.csv"):
    """Export matches to CSV."""
    try:
        result = monitor.export_matches_csv(filename)
        if result:
            return {"message": f"Exported matches to {filename}", "success": True}
        else:
            return {"message": "Error exporting matches", "success": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting matches: {str(e)}")

@app.post("/cleanup", response_model=MessageResponse)
async def cleanup_database():
    """Clean up the database."""
    try:
        deleted = monitor.cleanup_database()
        return {"message": f"Database cleanup: removed {deleted} old entries", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up database: {str(e)}")

@app.get("/logs", response_model=List[str])
async def get_logs(limit: int = 100):
    """Get recent logs."""
    try:
        with open('twitter_monitor.log', 'r') as f:
            logs = f.readlines()
        return logs[-limit:] if limit < len(logs) else logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")

@app.post("/check", response_model=MessageResponse)
async def check_now():
    """Run a check immediately."""
    try:
        # Run the monitoring job directly
        await monitor_job()
        return {"message": "Check completed", "success": True}
    except Exception as e:
        logger.error(f"Error running immediate check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error running check: {str(e)}")

async def status_event_generator():
    """Generate status events for SSE."""
    while True:
        try:
            # Get current status
            is_running, next_run, uptime = get_job_status()
            status_data = {
                "is_running": is_running,
                "next_run": next_run.isoformat() if next_run else None,
                "uptime": uptime
            }
            
            # Send status update
            yield f"data: {json.dumps(status_data)}\n\n"
            
            # Wait before next update
            await asyncio.sleep(5)  # Update every 5 seconds
        except Exception as e:
            logger.error(f"Error in status event generator: {str(e)}")
            await asyncio.sleep(5)  # Wait before retry

async def match_event_generator():
    """Generate match events for SSE."""
    while True:
        try:
            # Wait for new match
            match_data = await match_updates.get()
            yield f"data: {json.dumps(match_data)}\n\n"
        except Exception as e:
            logger.error(f"Error in match event generator: {str(e)}")
            await asyncio.sleep(1)  # Wait before retry

async def log_event_generator():
    """Generate log events for SSE."""
    # Send initial logs from buffer
    for log_entry in log_buffer:
        yield f"data: {json.dumps({'log': log_entry})}\n\n"
    
    # Create a queue for new logs
    log_queue = asyncio.Queue()
    
    # Add queue to a set of active queues
    active_queues.add(log_queue)
    try:
        while True:
            # Wait for new log entry
            log_entry = await log_queue.get()
            yield f"data: {json.dumps({'log': log_entry})}\n\n"
    finally:
        # Remove queue when client disconnects
        active_queues.remove(log_queue)

# Set to keep track of active log queues
active_queues = set()

@app.get("/stream/status")
async def stream_status():
    """Stream status updates via SSE."""
    return StreamingResponse(
        status_event_generator(),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )

@app.get("/stream/matches")
async def stream_matches():
    """Stream new matches via SSE."""
    return StreamingResponse(
        match_event_generator(),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )

@app.get("/stream/logs")
async def stream_logs():
    """Stream log updates via SSE."""
    return StreamingResponse(
        log_event_generator(),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )

# Add log management endpoints
@app.post("/logs/clear", response_model=MessageResponse)
async def clear_logs():
    """Clear the log file."""
    try:
        # Clear the log buffer
        log_buffer.clear()
        
        # Truncate the log file
        async with aiofiles.open('twitter_monitor.log', 'w') as f:
            await f.write('')
        
        logger.info("Log file cleared")
        return {"message": "Logs cleared successfully", "success": True}
    except Exception as e:
        logger.error(f"Error clearing logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear logs: {str(e)}")

@app.get("/logs/download")
async def download_logs():
    """Download the log file."""
    try:
        return StreamingResponse(
            aiofiles.open('twitter_monitor.log', mode='rb'),
            media_type='text/plain',
            headers={'Content-Disposition': f'attachment; filename=twitter_monitor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'}
        )
    except Exception as e:
        logger.error(f"Error downloading logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download logs: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)