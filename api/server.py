"""
FastAPI server for notification service REST API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.routes import router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Notification Service API",
        description="REST API for manually triggering event notifications",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure this properly in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(router, prefix="/api", tags=["notifications"])
    
    @app.on_event("startup")
    async def startup_event():
        logger.info("Notification Service API started")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Notification Service API shutting down")
    
    return app


# Create app instance
app = create_app()
