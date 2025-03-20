#!/usr/bin/env python3
import os
import json
import asyncio
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from twitter_monitor import TwitterMonitor

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

# Background monitoring process
monitoring_process = None

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

# Helper functions
def is_monitor_running():
    """Check if the monitor process is running."""
    pid_file = 'twitter_monitor.pid'
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 0)  # Check if process exists
            return True, pid
        except ProcessLookupError:
            os.remove(pid_file)
    return False, None

def start_monitor_process():
    """Start the monitor process in the background."""
    global monitoring_process
    if monitoring_process is not None and monitoring_process.poll() is None:
        return  # Process is already running
    
    # Start in a new process
    monitoring_process = subprocess.Popen(
        ["python", "cli.py", "start"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )

def stop_monitor_process():
    """Stop the monitor process."""
    is_running, pid = is_monitor_running()
    if is_running and pid:
        try:
            os.kill(pid, 15)  # SIGTERM
            if os.path.exists('twitter_monitor.pid'):
                os.remove('twitter_monitor.pid')
            return True
        except ProcessLookupError:
            if os.path.exists('twitter_monitor.pid'):
                os.remove('twitter_monitor.pid')
    return False

# API Routes
@app.get("/", response_model=MessageResponse)
async def root():
    """Root endpoint to check if API is running."""
    return {"message": "Twitter Monitor API is running", "success": True}

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get the current status of the monitor."""
    is_running, pid = is_monitor_running()
    
    # Get config info
    usernames = monitor.config["monitoring"]["usernames"]
    patterns = monitor.config["monitoring"]["regex_patterns"]
    keywords = monitor.config["monitoring"]["keywords"]
    interval = monitor.config["monitoring"]["check_interval_minutes"]
    
    # Get uptime if running
    uptime = None
    last_check = None
    if is_running and pid:
        try:
            with open('twitter_monitor.log', 'r') as f:
                logs = f.readlines()
                for line in reversed(logs):
                    if "Checking" in line and "users for updates" in line:
                        last_check = line.split(']')[0].strip('[')
                        break
        except:
            pass
    
    return {
        "is_running": is_running,
        "pid": pid,
        "uptime": uptime,
        "monitored_users": len(usernames),
        "regex_patterns": len(patterns),
        "keywords": len(keywords),
        "check_interval": interval,
        "last_check": last_check
    }

@app.post("/start", response_model=MessageResponse)
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start the monitoring process."""
    is_running, _ = is_monitor_running()
    if is_running:
        return {"message": "Monitoring is already running", "success": False}
    
    # Check if configuration is complete
    if (not monitor.config["twitter"]["api_key"] or 
        not monitor.config["telegram"]["bot_token"]):
        raise HTTPException(status_code=400, detail="Configuration incomplete. Please configure API keys first.")
    
    # Start monitoring in background
    background_tasks.add_task(start_monitor_process)
    
    return {"message": "Monitoring started", "success": True}

@app.post("/stop", response_model=MessageResponse)
async def stop_monitoring():
    """Stop the monitoring process."""
    success = stop_monitor_process()
    if success:
        return {"message": "Monitoring stopped", "success": True}
    else:
        return {"message": "Monitoring is not running", "success": False}

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

@app.post("/check", response_model=MessageResponse)
async def check_now(background_tasks: BackgroundTasks):
    """Run a check immediately."""
    try:
        background_tasks.add_task(monitor.check_tweets)
        return {"message": "Check started", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting check: {str(e)}")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)