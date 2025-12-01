"""
Unit tests for DTO models.
"""
import pytest
from models.dto import BookingBatchResponse, Event, NotificationMessage
import json


class TestBookingBatchResponse:
    """Test suite for BookingBatchResponse model."""
    
    def test_from_dict_complete_data(self):
        """Test creating BookingBatchResponse from complete dictionary."""
        data = {
            "booking_id": "booking-123",
            "event_id": "event-456",
            "user_id": "user-789",
            "user_email": "test@example.com",
            "event_name": "Test Event",
            "booking_time": "2025-11-30T10:00:00",
            "status": "confirmed"
        }
        
        booking = BookingBatchResponse.from_dict(data)
        
        assert booking.booking_id == "booking-123"
        assert booking.event_id == "event-456"
        assert booking.user_id == "user-789"
        assert booking.user_email == "test@example.com"
        assert booking.event_name == "Test Event"
        assert booking.booking_time == "2025-11-30T10:00:00"
        assert booking.status == "confirmed"
    
    def test_from_dict_minimal_data(self):
        """Test creating BookingBatchResponse with minimal required fields."""
        data = {
            "booking_id": "booking-123",
            "event_id": "event-456",
            "user_id": "user-789",
            "user_email": "test@example.com"
        }
        
        booking = BookingBatchResponse.from_dict(data)
        
        assert booking.booking_id == "booking-123"
        assert booking.event_id == "event-456"
        assert booking.user_id == "user-789"
        assert booking.user_email == "test@example.com"
        assert booking.event_name is None
        assert booking.booking_time is None
        assert booking.status == "confirmed"  # default value
    
    def test_email_property(self):
        """Test email property returns user_email."""
        booking = BookingBatchResponse(
            booking_id="b1",
            event_id="e1",
            user_id="u1",
            user_email="user@test.com"
        )
        
        assert booking.email == "user@test.com"
        assert booking.email == booking.user_email
    
    def test_name_property_extracts_from_email(self):
        """Test name property extracts username from email."""
        booking = BookingBatchResponse(
            booking_id="b1",
            event_id="e1",
            user_id="u1",
            user_email="johndoe@example.com"
        )
        
        assert booking.name == "johndoe"
    
    def test_name_property_handles_missing_email(self):
        """Test name property with empty email."""
        booking = BookingBatchResponse(
            booking_id="b1",
            event_id="e1",
            user_id="u1",
            user_email=""
        )
        
        assert booking.name == "User"


class TestEvent:
    """Test suite for Event model."""
    
    def test_from_dict_complete_data(self):
        """Test creating Event from complete dictionary."""
        data = {
            "event_id": "event-123",
            "event_name": "Test Event",
            "description": "A test event",
            "start_time": "2025-12-01T10:00:00",
            "end_time": "2025-12-01T12:00:00",
            "organizer_id": "org-456",
            "location": "Test Room",
            "remaining_seats": 10,
            "reminder_type": "one_day"
        }
        
        event = Event.from_dict(data)
        
        assert event.event_id == "event-123"
        assert event.event_name == "Test Event"
        assert event.description == "A test event"
        assert event.start_time == "2025-12-01T10:00:00"
        assert event.end_time == "2025-12-01T12:00:00"
        assert event.organizer_id == "org-456"
        assert event.location == "Test Room"
        assert event.remaining_seats == 10
        assert event.reminder_type == "one_day"
    
    def test_get_formatted_start_time(self):
        """Test formatted start time output."""
        event = Event(
            event_id="e1",
            event_name="Test",
            description=None,
            start_time="2025-12-01T10:30:00",
            end_time="2025-12-01T12:00:00",
            organizer_id="org1",
            location="Room A",
            remaining_seats=5
        )
        
        formatted = event.get_formatted_start_time()
        assert "December" in formatted
        assert "2025" in formatted


class TestNotificationMessage:
    """Test suite for NotificationMessage model."""
    
    def test_from_json_valid_message(self):
        """Test creating NotificationMessage from valid JSON."""
        json_str = json.dumps({
            "type": "event_created",
            "event": {
                "event_id": "event-123",
                "event_name": "Test Event",
                "description": "Test description",
                "start_time": "2025-12-01T10:00:00",
                "end_time": "2025-12-01T12:00:00",
                "organizer_id": "org-123",
                "location": "Test Room",
                "remaining_seats": 10
            }
        })
        
        message = NotificationMessage.from_json(json_str)
        
        assert message.type == "event_created"
        assert message.event.event_id == "event-123"
        assert message.event.event_name == "Test Event"
    
    def test_from_json_invalid_json(self):
        """Test error handling for invalid JSON."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            NotificationMessage.from_json("not valid json")
    
    def test_from_json_missing_type(self):
        """Test error handling for missing type field."""
        json_str = json.dumps({
            "event": {"event_id": "e1", "event_name": "Test"}
        })
        
        with pytest.raises(ValueError, match="Missing required field: 'type'"):
            NotificationMessage.from_json(json_str)
    
    def test_from_json_missing_event(self):
        """Test error handling for missing event field."""
        json_str = json.dumps({
            "type": "event_created"
        })
        
        with pytest.raises(ValueError, match="Missing required field: 'event'"):
            NotificationMessage.from_json(json_str)
    
    def test_from_json_invalid_event_type(self):
        """Test error handling for invalid event type."""
        json_str = json.dumps({
            "type": "invalid_type",
            "event": {"event_id": "e1"}
        })
        
        with pytest.raises(ValueError, match="Invalid event type"):
            NotificationMessage.from_json(json_str)
    
    def test_str_representation(self):
        """Test string representation of NotificationMessage."""
        event = Event(
            event_id="e1",
            event_name="Test Event",
            description=None,
            start_time="2025-12-01T10:00:00",
            end_time="2025-12-01T12:00:00",
            organizer_id="org1",
            location="Room",
            remaining_seats=5
        )
        message = NotificationMessage(type="event_created", event=event)
        
        str_repr = str(message)
        assert "event_created" in str_repr
        assert "e1" in str_repr
        assert "Test Event" in str_repr
