"""
LavinMQ consumer using pika (AMQP protocol).
"""
import pika
import json
import asyncio
from models.dto import NotificationMessage
from processor.notification_processor import NotificationProcessor
from data.repository import ParticipantRepository
from config.settings import settings
import logging
import signal
import sys

logger = logging.getLogger(__name__)


class QueueListener:
    """LavinMQ/RabbitMQ consumer that listens for notification messages."""
    
    def __init__(self):
        """Initialize queue listener with LavinMQ configuration."""
        self.config = settings.lavinmq
        self.connection = None
        self.channel = None
        self.should_stop = False
        self.processor = NotificationProcessor()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(
            f"QueueListener initialized for queue: {self.config.queue_name}"
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.should_stop = True
        self.stop()
    
    def connect(self):
        """Establish connection to LavinMQ."""
        try:
            # Create connection credentials
            credentials = pika.PlainCredentials(
                username=self.config.username,
                password=self.config.password
            )
            
            # Create connection parameters
            parameters = pika.ConnectionParameters(
                host=self.config.host,
                port=self.config.port,
                virtual_host=self.config.virtual_host,
                credentials=credentials,
                heartbeat=600,  # 10 minutes
                blocked_connection_timeout=300  # 5 minutes
            )
            
            # Establish connection
            logger.info(
                f"Connecting to LavinMQ at {self.config.host}:{self.config.port}..."
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare queue (idempotent - will create if doesn't exist)
            self.channel.queue_declare(
                queue=self.config.queue_name,
                durable=True  # Survive broker restart
            )
            
            # Set QoS to process one message at a time
            self.channel.basic_qos(prefetch_count=1)
            
            logger.info("Successfully connected to LavinMQ")
            
        except Exception as e:
            logger.error(f"Failed to connect to LavinMQ: {e}")
            raise
    
    def _on_message(self, channel, method, properties, body):
        """
        Callback when a message is received from the queue.
        
        Args:
            channel: Pika channel
            method: Delivery method
            properties: Message properties
            body: Message body (bytes)
        """
        try:
            # Decode message
            message_str = body.decode('utf-8')
            logger.info(f"Received message: {message_str}")
            
            # Parse JSON to check message type
            message_data = json.loads(message_str)
            
            # Handle event_reminder messages specially
            if message_data.get('type') == 'event_reminder':
                # For reminders, we need to fetch event details from database
                event_id = message_data.get('event_id')
                reminder_type = message_data.get('reminder_type')
                
                if not event_id or not reminder_type:
                    logger.error("Reminder message missing event_id or reminder_type")
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                # Fetch event details from database
                
                with ParticipantRepository() as repo:
                    # Get one participant to extract event details
                    participants = repo.get_participants_by_event(event_id, offset=0, limit=1)
                    
                    if not participants:
                        logger.warning(f"No participants found for event {event_id}, skipping reminder")
                        channel.basic_ack(delivery_tag=method.delivery_tag)
                        return
                    
                    # Extract event details from participant
                    participant = participants[0]
                    event_name = participant.event_name or "Event"
                    
                    # Construct full message with event object
                    full_message = {
                        "type": "event_reminder",
                        "event": {
                            "event_id": event_id,
                            "event_name": event_name,
                            "description": None,
                            "start_time": "",
                            "end_time": "",
                            "organizer_id": "",
                            "location": "",
                            "remaining_seats": 0,
                            "reminder_type": reminder_type
                        }
                    }
                    
                    message_str = json.dumps(full_message)
                    logger.info(f"Enriched reminder message with event details")
            
            # Parse message into DTO
            message = NotificationMessage.from_json(message_str)
            
            # Process the message
            asyncio.run(self.processor.process(message))
            
            # Acknowledge message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Message processed and acknowledged: {message}")
            
        except ValueError as e:
            logger.error(f"Invalid message format: {e}")
            # Acknowledge invalid messages to remove them from queue
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            # Negative acknowledgment - message will be requeued
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start(self):
        """Start listening for messages."""
        try:
            if not self.connection or self.connection.is_closed:
                self.connect()
            
            logger.info(
                f"Starting to consume messages from queue: {self.config.queue_name}"
            )
            
            # Start consuming messages
            self.channel.basic_consume(
                queue=self.config.queue_name,
                on_message_callback=self._on_message,
                auto_ack=False  # Manual acknowledgment
            )
            
            logger.info("Waiting for messages. Press CTRL+C to exit.")
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping...")
            self.stop()
        except Exception as e:
            logger.error(f"Error in consumer: {e}", exc_info=True)
            raise
    
    def stop(self):
        """Stop listening and close connections gracefully."""
        logger.info("Stopping queue listener...")
        
        try:
            if self.channel and self.channel.is_open:
                self.channel.stop_consuming()
                self.channel.close()
                logger.info("Channel closed")
        except Exception as e:
            logger.error(f"Error closing channel: {e}")
        
        try:
            if self.connection and self.connection.is_open:
                self.connection.close()
                logger.info("Connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
        
        logger.info("Queue listener stopped")
