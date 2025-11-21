"""
Queue publisher for sending reminder messages to LavinMQ.
"""
import pika
import json
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class QueuePublisher:
    """Publisher for sending messages to LavinMQ queue."""
    
    def __init__(self):
        """Initialize queue publisher with configuration."""
        self.config = settings.lavinmq
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Establish connection to LavinMQ."""
        try:
            credentials = pika.PlainCredentials(
                self.config.username,
                self.config.password
            )
            
            parameters = pika.ConnectionParameters(
                host=self.config.host,
                port=self.config.port,
                virtual_host=self.config.virtual_host,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare queue (idempotent)
            self.channel.queue_declare(
                queue=self.config.queue_name,
                durable=True
            )
            
            logger.debug(f"Connected to LavinMQ at {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to LavinMQ: {e}")
            raise
    
    def publish_reminder(self, event_id: str, reminder_type: str) -> bool:
        """
        Publish reminder message to queue.
        
        Args:
            event_id: Event ID (UUID)
            reminder_type: Type of reminder ('one_day' or 'one_hour')
            
        Returns:
            True if published successfully
        """
        try:
            # Ensure connection
            if not self.connection or self.connection.is_closed:
                self.connect()
            
            # Create message - convert event_id to string to handle UUID objects
            message = {
                "type": "event_reminder",
                "event_id": str(event_id),  # Convert to string for JSON serialization
                "reminder_type": reminder_type
            }
            
            # Publish to queue
            self.channel.basic_publish(
                exchange='',
                routing_key=self.config.queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            
            logger.info(
                f"Published reminder: event_id={event_id}, "
                f"type={reminder_type}"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to publish reminder for event {event_id}: {e}"
            )
            return False
    
    def close(self):
        """Close connection to LavinMQ."""
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
            if self.connection and self.connection.is_open:
                self.connection.close()
            logger.debug("Queue publisher connection closed")
        except Exception as e:
            logger.error(f"Error closing queue publisher: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
