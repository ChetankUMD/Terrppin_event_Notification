"""
API routes for manual notification triggers.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import logging
import asyncio

from processor.notification_processor import NotificationProcessor
from models.dto import Event, NotificationMessage

logger = logging.getLogger(__name__)

router = APIRouter()


class SendNotificationRequest(BaseModel):
    """Request model for sending notifications."""
    event_id: str
    notification_type: str = "event_updated"  # event_created, event_updated, event_cancelled, event_reminder


class SendNotificationResponse(BaseModel):
    """Response model for notification sending."""
    success: bool
    message: str
    event_id: str
    emails_sent: Optional[int] = None
    errors: Optional[int] = None


async def process_notification_async(event_id: str, notification_type: str):
    """Process notification asynchronously in background."""
    try:
        logger.info(f"Processing notification for event_id={event_id}, type={notification_type}")
        
        # Import here to avoid circular imports
        from data.database import get_session, close_session
        from sqlalchemy import text
        
        # Fetch event details from database
        session = get_session()
        try:
            query = text("""
                SELECT event_id, event_name, description, start_time, end_time, 
                       organizer_id, location, remaining_seats
                FROM events
                WHERE event_id = :event_id
            """)
            
            result = session.execute(query, {"event_id": event_id})
            row = result.fetchone()
            
            if not row:
                logger.error(f"Event not found: {event_id}")
                return
            
            # Create Event object
            event = Event(
                event_id=row.event_id,
                event_name=row.event_name,
                description=row.description,
                start_time=str(row.start_time) if row.start_time else None,
                end_time=str(row.end_time) if row.end_time else None,
                organizer_id=row.organizer_id,
                location=row.location,
                remaining_seats=row.remaining_seats
            )
            
            # Create notification message
            message = NotificationMessage(
                type=notification_type,
                event=event
            )
            
            # Process notification
            processor = NotificationProcessor()
            await processor.process(message)
            
            logger.info(f"Successfully processed notification for event_id={event_id}")
            
        finally:
            close_session(session)
            
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
        request: Contains event_id and notification_type
        background_tasks: FastAPI background tasks
        
    Returns:
        Response with success status and message
    """
    try:
        logger.info(
            f"Received notification request: event_id={request.event_id}, "
            f"type={request.notification_type}"
        )
        
        # Validate notification type
        valid_types = ["event_created", "event_updated", "event_cancelled", "event_reminder"]
        if request.notification_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid notification_type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Queue the notification processing in background
        background_tasks.add_task(
            process_notification_async,
            request.event_id,
            request.notification_type
        )
        
        return SendNotificationResponse(
            success=True,
            message=f"Notification processing queued for event {request.event_id}",
            event_id=request.event_id
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
