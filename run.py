"""
Application entry point for the notification service.
Initializes database, starts reminder scheduler, and starts the LavinMQ consumer.
"""
import logging
import signal
import sys
from data.database import init_database
from consumer.queue_listener import QueueListener
from scheduler.reminder_scheduler import start_reminder_scheduler, stop_reminder_scheduler
from config.settings import settings


def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=settings.log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('notification_service.log')
        ]
    )


# Global variables for graceful shutdown
scheduler = None
listener = None


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info("Shutdown signal received, stopping services...")
    
    # Stop scheduler
    if scheduler:
        stop_reminder_scheduler(scheduler)
    
    # Stop queue listener
    if listener:
        listener.stop()
    
    logger.info("Services stopped gracefully")
    sys.exit(0)


def main():
    """Main application entry point."""
    global scheduler, listener
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Starting Notification Service")
    logger.info("=" * 60)
    
    try:
        
        # Initialize database
        logger.info("Initializing database...")
        init_database()
        logger.info("Database initialized successfully")
        
        # Start reminder scheduler
        logger.info("Starting reminder scheduler...")
        scheduler = start_reminder_scheduler()
        logger.info("Reminder scheduler started (runs every 1 minute)")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create and start queue listener (blocking)
        logger.info("Starting queue listener...")
        listener = QueueListener()
        listener.start()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        if scheduler:
            stop_reminder_scheduler(scheduler)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        if scheduler:
            stop_reminder_scheduler(scheduler)
        sys.exit(1)
    finally:
        logger.info("=" * 60)
        logger.info("Notification Service Stopped")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
