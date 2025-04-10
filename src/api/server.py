"""XCA-Bot API Server

This module handles starting the FastAPI application and managing service instances.
"""

import uvicorn
from src.core.logger import logger, dev_log
from src.api.app import app
from src.core.monitor import MonitorService

# Global service instance for API routes
_monitor_service = None

def get_monitor_service():
    """Get the global monitor service instance."""
    return _monitor_service

async def start_api_server(host: str, port: int, monitor_service: MonitorService = None):
    """Start the FastAPI server with the provided monitor service.
    
    Args:
        host: Host to bind to
        port: Port to listen on
        monitor_service: Initialized MonitorService instance
    """
    global _monitor_service
    _monitor_service = monitor_service
    
    dev_log(f"Starting API server on {host}:{port}", "INFO")
    
    config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve() 