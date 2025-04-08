"""
XCA-Bot - Twitter Cryptocurrency Address Monitor

Main application entry point for the XCA-Bot system.
This module initializes the core services and starts the API server.
"""

import os
import sys
import argparse
import asyncio
import uvicorn
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

from src.core.logger import logger, dev_log, setup_logging
from src.core.monitor import MonitorService
from src.models.config import AppConfig
from src.db.repository import DatabaseRepository

# Load environment variables
load_dotenv()

# Global monitor service instance
monitor_service: Optional[MonitorService] = None


async def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load configuration from YAML file and/or environment variables.
    
    Args:
        config_path: Path to YAML configuration file (optional)
        
    Returns:
        AppConfig: Application configuration
        
    Environment variables take precedence over YAML configuration.
    If no config_path is provided, configuration is loaded from environment variables only.
    """
    # First check if we have a YAML config file
    config_dict = {}
    
    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            dev_log(f"Loading configuration from {config_path}", "INFO")
            try:
                with open(config_file, 'r') as file:
                    config_dict = yaml.safe_load(file) or {}
            except Exception as e:
                logger.error(f"Failed to load YAML configuration: {str(e)}")
                dev_log(f"YAML configuration error: {str(e)}", "ERROR")
                # Continue with empty config_dict so we can still use environment variables
    
    # Now load and merge with environment variables (which take precedence)
    try:
        if config_dict:
            # Merge YAML config with environment variables
            config = AppConfig.from_yaml_and_env(config_dict)
            dev_log("Configuration loaded from YAML and environment variables", "INFO")
        else:
            # Load from environment variables only
            config = AppConfig.from_env()
            dev_log("Configuration loaded from environment variables", "INFO")
        
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        dev_log(f"Configuration error: {str(e)}", "ERROR")
        raise


async def initialize_services(config: AppConfig) -> MonitorService:
    """Initialize all required services."""
    dev_log("Initializing services", "INFO")
    
    # Create monitor service
    monitor = MonitorService()
    
    # Initialize it
    await monitor.init(config)
    
    if not monitor.initialized:
        error_msg = "Failed to initialize monitor service"
        logger.error(error_msg)
        dev_log(error_msg, "ERROR")
        raise RuntimeError(error_msg)
    
    return monitor


async def startup(config_path: Optional[str] = None, auto_start: bool = False) -> MonitorService:
    """Startup sequence for the application."""
    # Set up logging
    setup_logging()
    
    dev_log("Starting XCA-Bot", "INFO")
    
    try:
        # Load configuration
        config = await load_config(config_path)
        
        # Initialize services
        monitor = await initialize_services(config)
        
        # Auto-start monitoring if requested
        if auto_start:
            dev_log("Auto-starting monitoring", "INFO")
            await monitor.start_monitoring()
        
        return monitor
    
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}", exc_info=True)
        dev_log(f"Startup error: {str(e)}", "ERROR")
        raise


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="XCA-Bot - Twitter Cryptocurrency Address Monitor")
    parser.add_argument(
        "--config", 
        default=None, 
        help="Path to YAML configuration file (default: use environment variables only)"
    )
    parser.add_argument(
        "--auto-start", 
        action="store_true", 
        help="Start monitoring automatically"
    )
    parser.add_argument(
        "--host", 
        default=os.getenv("API_HOST", "127.0.0.1"), 
        help="API server host (default: from API_HOST env var or 127.0.0.1)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=int(os.getenv("API_PORT", "8000")), 
        help="API server port (default: from API_PORT env var or 8000)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    
    # Set up the event loop
    loop = asyncio.get_event_loop()
    
    try:
        # Initialize the application
        monitor_service = loop.run_until_complete(startup(args.config, args.auto_start))
        
        # Start the API server
        dev_log(f"Starting API server on {args.host}:{args.port}", "INFO")
        uvicorn.run(
            "src.api.app:app",
            host=args.host,
            port=args.port,
            log_level="info"
        )
    
    except KeyboardInterrupt:
        dev_log("Received keyboard interrupt, shutting down", "INFO")
        if monitor_service and monitor_service.initialized:
            loop.run_until_complete(monitor_service.stop_monitoring())
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        dev_log(f"Application error: {str(e)}", "ERROR")
        sys.exit(1)
    
    finally:
        dev_log("XCA-Bot shutdown complete", "INFO") 