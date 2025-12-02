"""
API routes for manual notification triggers.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import logging

from processor.notification_processor import NotificationProcessor
from models.dto import Event, NotificationMessage

logger = logging.getLogger(__name__)

router = APIRouter()


class EventData(BaseModel):
    """Event data model."""
    event_id: str
    event_name: str
    description: Optional[str] = None
    start_time: str
    end_time: str
    organizer_id: str
    location: str
    remaining_seats: int
    reminder_type: Optional[str] = None


class SendNotificationRequest(BaseModel):
    """Request model for sending notifications."""
    type: str  # event_created, event_updated, event_update, event_cancelled, event_reminder
    event: EventData


class SendNotificationResponse(BaseModel):
    """Response model for notification sending."""
    success: bool
    message: str
    event_id: str
    emails_sent: Optional[int] = None
    errors: Optional[int] = None


async def process_notification_async(notification_type: str, event_data: dict):
    """Process notification asynchronously in background."""
    try:
        logger.info(f"Processing notification for event_id={event_data.get('event_id')}, type={notification_type}")
        
        # Create Event object from provided data
        event = Event(
            event_id=event_data.get('event_id', ''),
            event_name=event_data.get('event_name', ''),
            description=event_data.get('description'),
            start_time=event_data.get('start_time', ''),
            end_time=event_data.get('end_time', ''),
            organizer_id=event_data.get('organizer_id', ''),
            location=event_data.get('location', ''),
            remaining_seats=event_data.get('remaining_seats', 0),
            reminder_type=event_data.get('reminder_type')
        )
        
        # Create notification message
        message = NotificationMessage(
            type=notification_type,
            event=event
        )
        
        # Process notification
        processor = NotificationProcessor()
        await processor.process(message)
        
        logger.info(f"Successfully processed notification for event_id={event_data.get('event_id')}")
            
    except Exception as e:
        logger.error(f"Error processing notification: {e}", exc_info=True)


@router.post("/notifications/send", response_model=SendNotificationResponse)
async def send_notification(
    request: SendNotificationRequest,
    background_tasks: BackgroundTasks
):
    """
    Manually trigger notifications for a specific event.
    
    Args:
        request: Contains type and event data
        background_tasks: FastAPI background tasks
        
    Returns:
        Response with success status and message
    """
    try:
        logger.info(
            f"Received notification request: event_id={request.event.event_id}, "
            f"type={request.type}"
        )
        
        # Validate notification type
        valid_types = ["event_created", "event_updated", "event_update", "event_cancelled", "event_reminder"]
        if request.type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Convert EventData to dict for background task
        event_dict = request.event.model_dump()
        
        # Queue the notification processing in background
        background_tasks.add_task(
            process_notification_async,
            request.type,
            event_dict
        )
        
        return SendNotificationResponse(
            success=True,
            message=f"Notification processing queued for event {request.event.event_id}",
            event_id=request.event.event_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send_notification endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue notification: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "notification-service",
        "version": "1.0.0"
    }
