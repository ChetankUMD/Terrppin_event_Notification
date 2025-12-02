"""
Unified entry point for the Notification Service.
Runs both the FastAPI server and the background services (Queue Listener, Scheduler).
"""
import logging
import threading
import uvicorn
import os
import sys

# Add current directory to path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.main import app
from data.database import init_database
from scheduler.reminder_scheduler import start_reminder_scheduler, stop_reminder_scheduler
from consumer.queue_listener import QueueListener
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format=settings.log_format,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('notification_service.log')
    ]
)

logger = logging.getLogger(__name__)

# Global variables to hold references
scheduler = None
listener = None
listener_thread = None

@app.on_event("startup")
async def startup_services():
    """Start background services when API starts."""
    global scheduler, listener, listener_thread
    logger.info("Initializing background services...")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_database()
        
        # Start scheduler
        logger.info("Starting reminder scheduler...")
        scheduler = start_reminder_scheduler()
        
        # Start queue listener in a separate thread
        logger.info("Starting queue listener...")
        listener = QueueListener()
        listener_thread = threading.Thread(target=listener.start, daemon=True)
        listener_thread.start()
        logger.info("Queue listener started in background thread")
        
    except Exception as e:
        logger.error(f"Failed to start services: {e}", exc_info=True)
        # We might want to exit here if services are critical
        sys.exit(1)

@app.on_event("shutdown")
async def shutdown_services():
    """Stop background services when API stops."""
    global scheduler, listener
    logger.info("Shutting down background services...")
    
    if scheduler:
        logger.info("Stopping scheduler...")
        stop_reminder_scheduler(scheduler)
    
    if listener:
        logger.info("Stopping queue listener...")
        listener.stop()
        if listener_thread and listener_thread.is_alive():
            listener_thread.join(timeout=5.0)
            logger.info("Queue listener thread stopped")

if __name__ == "__main__":
    # Run the server
    # We use "main:app" because this file is named main.py
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=int(os.getenv("PORT", 8000)),
        reload=False
    )
