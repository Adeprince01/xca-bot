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
    """Health check endpoint."""
    return {"status": "healthy"} 