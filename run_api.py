"""
Start the FastAPI server for the notification service.
Run this separately from run.py to have both API and queue listener running.
"""
import uvicorn
import logging
from config.settings import settings

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format
)

logger = logging.getLogger(__name__)


def main():
    """Start the API server."""
    logger.info("=" * 60)
    logger.info("Starting Notification Service API")
    logger.info(f"Host: {settings.api.host}")
    logger.info(f"Port: {settings.api.port}")
    logger.info("=" * 60)
    
    uvicorn.run(
        "api.server:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
