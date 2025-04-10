"""
XCA-Bot Main Application

This is the main application entry point for the XCA-Bot system.
"""

import os
import sys
import asyncio
import argparse
from typing import Optional, Tuple

import yaml
from src.core.logger import logger, dev_log
from src.core.monitor import MonitorService
from src.models.config import AppConfig
from src.api.server import start_api_server

# Global service instance
monitor_service: Optional[MonitorService] = None

async def load_config(config_path: str) -> Optional[AppConfig]:
    """Load configuration from YAML file and environment variables.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        AppConfig if successful, None if failed
    """
    try:
        if not os.path.exists(config_path):
            logger.error(f"Configuration file not found: {config_path}")
            return None
            
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            
        # Override with environment variables if present
        if 'TWITTER_BEARER_TOKEN' in os.environ:
            config_data['twitter']['bearer_token'] = os.environ['TWITTER_BEARER_TOKEN']
        if 'TELEGRAM_BOT_TOKEN' in os.environ:
            config_data['telegram']['bot_token'] = os.environ['TELEGRAM_BOT_TOKEN']
        if 'DATABASE_URL' in os.environ:
            config_data['database']['connection_string'] = os.environ['DATABASE_URL']
            
        return AppConfig.from_dict(config_data)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return None

async def initialize_services(config: AppConfig) -> Tuple[bool, str]:
    """Create and initialize the MonitorService.
    
    Args:
        config: Application configuration
        
    Returns:
        Tuple of (success: bool, error_message: str)
    """
    global monitor_service
    
    try:
        monitor_service = MonitorService()
        initialized = await monitor_service.init(config)
        
        if not initialized:
            status = monitor_service.status
            error_msg = "Service initialization failed:\n"
            if not status["database"]:
                error_msg += "- Database connection failed\n"
            if not status["twitter"]:
                error_msg += "- Twitter API initialization failed\n"
            if not status["telegram"]:
                error_msg += "- Telegram bot initialization failed\n"
            if status["last_error"]:
                error_msg += f"Last error: {status['last_error']}"
            return False, error_msg
            
        return True, ""
    except Exception as e:
        return False, f"Unexpected error during service initialization: {str(e)}"

async def startup(config_path: str, auto_start: bool = False) -> bool:
    """Application startup sequence.
    
    Args:
        config_path: Path to configuration file
        auto_start: Whether to start monitoring automatically
        
    Returns:
        bool: True if startup was successful
    """
    # Load configuration
    config = await load_config(config_path)
    if not config:
        return False
        
    # Initialize services
    success, error_msg = await initialize_services(config)
    if not success:
        logger.error(error_msg)
        return False
        
    # Start monitoring if requested
    if auto_start and monitor_service:
        if not await monitor_service.start_monitoring():
            logger.error("Failed to start monitoring")
            return False
            
    return True

# Rest of the application code below 