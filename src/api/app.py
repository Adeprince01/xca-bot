"""
XCA-Bot API Application

This module defines the FastAPI application for the XCA-Bot API.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import asyncio
from typing import Dict, Any, List, Optional

from src.core.logger import logger, dev_log
from src.api.routes import router as api_router
from src.models.config import AppConfig

# Create FastAPI app
app = FastAPI(
    title="XCA-Bot API",
    description="API for XCA-Bot - Twitter Cryptocurrency Address Monitor",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API router
app.include_router(api_router, prefix="/api/v1")

# Add middleware for request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware to add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions."""
    error_detail = str(exc)
    
    # Log the error
    logger.error(f"Unhandled exception: {error_detail}", exc_info=True)
    dev_log(f"API Error: {error_detail}", "ERROR")
    
    # Return a JSON response
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": error_detail,
        },
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint that redirects to documentation."""
    return {
        "name": "XCA-Bot API",
        "version": app.version,
        "documentation": "/docs",
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}

# Enhanced API health check endpoint that doesn't depend on monitor service
@app.get("/api/v1/health")
async def api_health_check():
    """API health check that reports detailed service status information."""
    try:
        from src.api.server import get_monitor_service
        monitor = get_monitor_service()
        monitor_available = monitor is not None
        
        # Get detailed service status if monitor is available
        services_status = {
            "monitor": {
                "available": monitor_available,
                "initialized": False,
                "running": False,
            }
        }
        
        if monitor_available:
            services_status["monitor"]["initialized"] = monitor.initialized
            services_status["monitor"]["running"] = monitor.is_running if hasattr(monitor, "is_running") else False
            
            # Add Twitter and Telegram service status if possible
            if hasattr(monitor, "twitter_service") and monitor.twitter_service:
                services_status["twitter"] = {
                    "available": True,
                    "initialized": monitor.twitter_service.initialized if hasattr(monitor.twitter_service, "initialized") else False,
                }
            else:
                services_status["twitter"] = {"available": False}
                
            if hasattr(monitor, "telegram_service") and monitor.telegram_service:
                services_status["telegram"] = {
                    "available": True,
                    "initialized": monitor.telegram_service.initialized if hasattr(monitor.telegram_service, "initialized") else False,
                }
            else:
                services_status["telegram"] = {"available": False}
                
            if hasattr(monitor, "db_repo") and monitor.db_repo:
                services_status["database"] = {
                    "available": True,
                    "connected": True if hasattr(monitor.db_repo, "connected") and monitor.db_repo.connected else "Unknown"
                }
            else:
                services_status["database"] = {"available": False}
                
    except Exception as e:
        monitor_available = False
        services_status = {
            "monitor": {"available": False, "error": str(e)},
            "twitter": {"available": False},
            "telegram": {"available": False},
            "database": {"available": False}
        }
    
    return {
        "status": "available",
        "api_version": app.version,
        "services": services_status,
        "timestamp": time.time()
    } 