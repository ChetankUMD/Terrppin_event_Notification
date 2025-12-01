# Notification Service REST API

## Overview

The notification service now exposes a REST API for manually triggering notifications!

## Starting the API Server

### Option 1: Run API Only
```bash
python run_api.py
```
The API will start on **port 8001** by default.

### Option 2: Run Both API and Queue Listener
```bash
# Terminal 1 - Queue Listener
python run.py

# Terminal 2 - API Server
python run_api.py
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## Endpoints

### POST `/api/notifications/send`

Manually trigger notifications for a specific event.

**Request Body:**
```json
{
  "event_id": "your-event-id-uuid",
  "notification_type": "event_updated"
}
```

**Notification Types:**
- `event_created` - Sent when event is first created
- `event_updated` - Sent when event details change
- `event_cancelled` - Sent when event is cancelled
- `event_reminder` - Sent as a reminder before event starts

**Response:**
```json
{
  "success": true,
  "message": "Notification processing queued for event abc-123",
  "event_id": "abc-123",
  "emails_sent": null,
  "errors": null
}
```

**Example cURL:**
```bash
curl -X POST "http://localhost:8001/api/notifications/send" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "f73dba20-5e86-4bcc-bdc5-8be7385cc06d",
    "notification_type": "event_updated"
  }'
```

**Example Python:**
```python
import requests

response = requests.post(
    "http://localhost:8001/api/notifications/send",
    json={
        "event_id": "f73dba20-5e86-4bcc-bdc5-8be7385cc06d",
        "notification_type": "event_updated"
    }
)

print(response.json())
```

### GET `/api/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "notification-service",
  "version": "1.0.0"
}
```

## Configuration

Set these environment variables in `.env`:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8001
API_ENABLED=True
```

## How It Works

1. **Request Received**: API receives event_id and notification type
2. **Validation**: Validates notification type  
3. **Background Processing**: Queues notification processing in background
4. **Database Query**: Fetches event details from events table
5. **Participant Lookup**: Gets all participants for that event
6. **Email Sending**: Sends emails to all participants
7. **Response**: Returns immediately with queued status

## Architecture

```
User/System
    ↓ POST /api/notifications/send
FastAPI Server (port 8001)
    ↓ Background Task
Notification Processor
    ↓ Queries
Database (events, bookings)
    ↓ Sends
Emails to Participants
```

## Testing

### Quick Test:
```bash
# Start the API
python run_api.py

# In another terminal, test the health endpoint
curl http://localhost:8001/api/health

# Test notification trigger (replace with your event_id)
curl -X POST "http://localhost:8001/api/notifications/send" \
  -H "Content-Type: application/json" \
  -d '{"event_id": "your-event-id", "notification_type": "event_updated"}'
```

## Notes

- The API runs **independently** from the queue listener
- Both can run simultaneously
- API processes notifications in the **background** (non-blocking)
- Responses are immediate; actual email sending happens asynchronously
