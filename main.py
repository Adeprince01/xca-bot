"""
XCA-Bot - Twitter Cryptocurrency Address Monitor

Main application entry point for the XCA-Bot system.
This module initializes the core services and starts the API server.
"""

import os
import sys
import argparse
import asyncio
import yaml
import time
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

from src.core.logger import logger, dev_log, setup_logger
from src.core.monitor import MonitorService
from src.models.config import AppConfig
from src.db.repository import DatabaseRepository
from src.api.server import start_api_server

# Load environment variables
load_dotenv()

# Global monitor service instance
monitor_service: Optional[MonitorService] = None

# Constants
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5


async def load_config(config_path: Optional[str] = None) -> Optional[AppConfig]:
    """Load configuration from YAML file and/or environment variables.
    
    Args:
        config_path: Path to YAML configuration file (optional)
        
    Returns:
        AppConfig: Application configuration or None if loading failed
        
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
        return None


async def initialize_services(config: AppConfig) -> Tuple[bool, str, Optional[MonitorService]]:
    """Initialize all required services.
    
    Args:
        config: Application configuration
        
    Returns:
        Tuple containing:
        - Success flag (True/False)
        - Error message (empty string if successful)
        - MonitorService instance (None if initialization failed)
    """
    dev_log("Initializing services", "INFO")
    
    try:
        # Create monitor service
        monitor = MonitorService()
        
        # Initialize it
        await monitor.init(config)
        
        if not monitor.initialized:
            error_msg = "Failed to initialize monitor service"
            logger.error(error_msg)
            dev_log(error_msg, "ERROR")
            return False, error_msg, None
        
        return True, "", monitor
    except Exception as e:
        error_msg = f"Error initializing services: {str(e)}"
        logger.error(error_msg, exc_info=True)
        dev_log(error_msg, "ERROR")
        return False, error_msg, None


async def initialize_services_with_retry(config: AppConfig) -> Tuple[bool, str, Optional[MonitorService]]:
    """Initialize services with a retry mechanism for resilience.
    
    Args:
        config: Application configuration
        
    Returns:
        Same as initialize_services()
    """
    attempt = 0
    last_error = ""
    
    while attempt < MAX_RETRY_ATTEMPTS:
        attempt += 1
        
        dev_log(f"Service initialization attempt {attempt}/{MAX_RETRY_ATTEMPTS}", "INFO")
        success, error_msg, monitor = await initialize_services(config)
        
        if success:
            if attempt > 1:
                dev_log(f"Successfully initialized services after {attempt} attempts", "INFO")
            return True, "", monitor
        
        last_error = error_msg
        
        if attempt < MAX_RETRY_ATTEMPTS:
            dev_log(f"Retrying service initialization in {RETRY_DELAY_SECONDS} seconds...", "INFO")
            await asyncio.sleep(RETRY_DELAY_SECONDS)
    
    return False, f"Failed to initialize services after {MAX_RETRY_ATTEMPTS} attempts. Last error: {last_error}", None


async def main():
    """Application main entry point."""
    global monitor_service
    
    # Set up logging
    setup_logger()
    
    # Parse command line arguments
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
    parser.add_argument(
        "--no-retry", 
        action="store_true", 
        help="Disable retry mechanism for service initialization"
    )
    args = parser.parse_args()
    
    dev_log("Starting XCA-Bot", "INFO")
    
    # Load configuration
    config = await load_config(args.config)
    if not config:
        logger.error("Failed to load configuration. Exiting.")
        return 1
    
    # Initialize services with retry mechanism unless disabled
    if args.no_retry:
        success, error_msg, monitor_service = await initialize_services(config)
    else:
        success, error_msg, monitor_service = await initialize_services_with_retry(config)
    
    if not success:
        logger.error(f"Service initialization failed: {error_msg}")
        return 1
    
    # Auto-start monitoring if requested
    if args.auto_start and monitor_service:
        dev_log("Auto-starting monitoring", "INFO")
        if not await monitor_service.start_monitoring():
            logger.error("Failed to start monitoring")
    
    # Start the API server (this will block until the server is shut down)
    try:
        await start_api_server(
            host=args.host,
            port=args.port,
            monitor_service=monitor_service
        )
    except KeyboardInterrupt:
        dev_log("Received keyboard interrupt, shutting down", "INFO")
        if monitor_service and monitor_service.initialized:
            await monitor_service.stop_monitoring()
    except Exception as e:
        logger.error(f"API server error: {str(e)}", exc_info=True)
        return 1
    
    dev_log("XCA-Bot shutdown complete", "INFO") 
    return 0


# Entry point for the application
if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 