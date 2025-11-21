# Notification Service

A production-quality Python notification system that consumes messages from LavinMQ (AMQP) and sends email notifications to event participants in batches.

## Features

- **LavinMQ Consumer**: Listens to `event_notifications` queue using pika (AMQP protocol)
- **Batch Processing**: Processes participants in configurable batches (default: 100)
- **Async Email Service**: Sends emails asynchronously with retry logic
- **Database Layer**: SQLAlchemy-based repository with pagination support
- **Email Templates**: HTML templates for UPDATED, CREATED, and CANCELLED events
- **Comprehensive Logging**: Detailed logs for every batch, failure, and retry
- **Graceful Shutdown**: Proper signal handling for clean shutdowns

## Project Structure

```
notification-service/
├── consumer/
│   └── queue_listener.py      # LavinMQ consumer
├── processor/
│   └── notification_processor.py  # Message processing logic
├── data/
│   ├── database.py            # SQLAlchemy setup and models
│   └── repository.py          # Participant repository
├── email_service/
│   └── email_service.py       # Async email sender
├── templates/
│   └── email_templates.py     # Email template loader
├── config/
│   └── settings.py            # Configuration management
├── models/
│   └── dto.py                 # Data transfer objects
├── run.py                     # Application entry point
├── requirements.txt           # Python dependencies
├── add_test_data.py           # Helper: Add test participants
├── send_test_message.py       # Helper: Send test messages
└── test_all_components.py     # Comprehensive test suite
```

## Installation

1. **Clone or navigate to the project directory**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the project root or set these variables in your environment:

### LavinMQ Configuration
```bash
LAVINMQ_HOST=localhost
LAVINMQ_PORT=5672
LAVINMQ_USERNAME=guest
LAVINMQ_PASSWORD=guest
LAVINMQ_QUEUE=event_notifications
LAVINMQ_VHOST=/
```

### Database Configuration
```bash
DATABASE_URL=sqlite:///notification_service.db
DATABASE_ECHO=False
```

### Email Configuration
```bash
# Dummy mode (for testing without real SMTP)
EMAIL_DUMMY_MODE=True

# Real SMTP configuration (set EMAIL_DUMMY_MODE=False to use)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=notifications@example.com
FROM_NAME=Notification Service
SMTP_USE_TLS=True
```

### Processor Configuration
```bash
BATCH_SIZE=100
MAX_RETRIES=3
RETRY_DELAY=5
```

### Logging Configuration
```bash
LOG_LEVEL=INFO
```

## Running the Application

1. **Start LavinMQ** (if not already running):
   ```bash
   # Using Docker
   docker run -d --name lavinmq -p 5672:5672 -p 15672:15672 cloudamqp/lavinmq
   ```

2. **Run the notification service**:
   ```bash
   python run.py
   ```

The service will:
- Initialize the database (create tables if they don't exist)
- Connect to LavinMQ
- Start listening for messages on the `event_notifications` queue

## Message Format

Send messages to the `event_notifications` queue in the following JSON format:

```json
{
  "type": "UPDATED",
  "event_id": 123
}
```

**Supported event types:**
- `UPDATED` - Event was updated
- `CREATED` - New event was created
- `CANCELLED` - Event was cancelled

## Testing

### 1. Add Test Participants

Create a Python script to add test participants:

```python
from data.database import init_database, get_session, close_session
from data.repository import ParticipantRepository

# Initialize database
init_database()

# Add test participants
with ParticipantRepository() as repo:
    for i in range(250):  # Add 250 participants for testing batches
        repo.add_participant(
            event_id=123,
            email=f"participant{i}@example.com",
            name=f"Participant {i}"
        )

print("Test participants added!")
```

### 2. Send Test Messages

Use the LavinMQ management UI (http://localhost:15672) or a Python script:

```python
import pika
import json

# Connect to LavinMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost')
)
channel = connection.channel()

# Declare queue
channel.queue_declare(queue='event_notifications', durable=True)

# Send test message
message = {
    "type": "UPDATED",
    "event_id": 123
}

channel.basic_publish(
    exchange='',
    routing_key='event_notifications',
    body=json.dumps(message),
    properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
)

print("Test message sent!")
connection.close()
```

### 3. Monitor Logs

Check the logs for processing details:
- Console output (stdout)
- `notification_service.log` file

## How It Works

1. **Message Reception**: The `QueueListener` receives messages from LavinMQ
2. **Deserialization**: JSON messages are deserialized into `NotificationMessage` DTOs
3. **Processing**: The `NotificationProcessor` handles each message:
   - Extracts event type and ID
   - Loads the appropriate email template
   - Fetches participants in batches (100 per batch)
   - Sends emails to all participants
4. **Email Sending**: The `EmailService` sends emails asynchronously with retry logic
5. **Acknowledgment**: Messages are acknowledged after successful processing

## Production Considerations

- **Database**: Switch from SQLite to PostgreSQL/MySQL for production
- **Email Service**: Configure real SMTP credentials and set `EMAIL_DUMMY_MODE=False`
- **Error Handling**: Consider implementing a dead letter queue for failed messages
- **Monitoring**: Add application monitoring (e.g., Prometheus, Datadog)
- **Scaling**: Run multiple instances for higher throughput
- **Security**: Use environment variables or secret management for credentials

## Logging

The application logs:
- Connection status to LavinMQ
- Each received message
- Batch processing progress
- Email sending results (success/failure)
- Retry attempts
- Errors and exceptions

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Graceful Shutdown

The application handles SIGINT (Ctrl+C) and SIGTERM signals gracefully:
- Stops consuming new messages
- Closes the channel
- Closes the connection
- Exits cleanly

## License

This is a production-quality example implementation.