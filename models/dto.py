"""
Data Transfer Objects for the notification service.
"""
from dataclasses import dataclass
from typing import Literal, Optional
from datetime import datetime
import json


EventType = Literal['event_updated', 'event_update', 'event_created', 'event_cancelled', 'event_reminder']


@dataclass
class BookingBatchResponse:
    """Booking data from the booking service API."""
    booking_id: str
    event_id: str
    user_id: str
    user_email: str
    event_name: Optional[str] = None
    booking_time: Optional[str] = None
    status: str = 'confirmed'
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BookingBatchResponse':
        """Create BookingBatchResponse from dictionary."""
        return cls(
            booking_id=data['booking_id'],
            event_id=data['event_id'],
            user_id=data['user_id'],
            user_email=data['user_email'],
            event_name=data.get('event_name'),
            booking_time=data.get('booking_time'),
            status=data.get('status', 'confirmed')
        )
    
    @property
    def email(self):
        """Alias for user_email for backward compatibility."""
        return self.user_email
    
    @property
    def name(self):
        """Extract name from email for backward compatibility."""
        return self.user_email.split('@')[0] if self.user_email else 'User'



@dataclass
class Event:
    """Event details from the message."""
    event_id: str
    event_name: str
    description: Optional[str]
    start_time: str
    end_time: str
    organizer_id: str
    location: str
    remaining_seats: int
    reminder_type: Optional[str] = None  # For event_reminder messages: 'one_day' or 'one_hour'
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Event':
        """Create Event from dictionary."""
        return cls(
            event_id=data['event_id'],
            event_name=data.get('event_name', ''),
            description=data.get('description'),
            start_time=data.get('start_time', ''),
            end_time=data.get('end_time', ''),
            organizer_id=data.get('organizer_id', ''),
            location=data.get('location', ''),
            remaining_seats=data.get('remaining_seats', 0),
            reminder_type=data.get('reminder_type')  # Optional for reminders
        )
    
    def get_formatted_start_time(self) -> str:
        """Get formatted start time."""
        try:
            dt = datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
            return dt.strftime('%B %d, %Y at %I:%M %p')
        except:
            return self.start_time
    
    def get_formatted_end_time(self) -> str:
        """Get formatted end time."""
        try:
            dt = datetime.fromisoformat(self.end_time.replace('Z', '+00:00'))
            return dt.strftime('%I:%M %p')
        except:
            return self.end_time


@dataclass
class NotificationMessage:
    """DTO for notification messages from the queue."""
    type: EventType
    event: Event
    
    @classmethod
    def from_json(cls, json_str: str) -> 'NotificationMessage':
        """
        Deserialize JSON string into NotificationMessage.
        
        Args:
            json_str: JSON string containing type and event
            
        Returns:
            NotificationMessage instance
            
        Raises:
            ValueError: If JSON is invalid or missing required fields
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        
        if 'type' not in data:
            raise ValueError("Missing required field: 'type'")
        if 'event' not in data:
            raise ValueError("Missing required field: 'event'")
        
        event_type = data['type']
        if event_type not in ['event_updated', 'event_update', 'event_created', 'event_cancelled', 'event_reminder']:
            raise ValueError(f"Invalid event type: {event_type}")
        
        try:
            event = Event.from_dict(data['event'])
        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid event data: {e}")
        
        return cls(type=event_type, event=event)
    
    def __str__(self) -> str:
        return f"NotificationMessage(type={self.type}, event_id={self.event.event_id}, event_name={self.event.event_name})"
