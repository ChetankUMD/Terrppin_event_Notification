"""
Unit tests for database module.
"""
import pytest
from unittest.mock import Mock, patch
from data.database import init_database, get_session, close_session, Participant


class TestDatabase:
    """Test suite for database module."""
    
    def test_participant_model_creation(self):
        """Test creating a Participant instance."""
        participant = Participant(
            booking_id="booking-123",
            event_id="event-456",
            user_id="user-789",
            user_email="user@example.com",
            event_name="Test Event",
            booking_time="2024-12-01T10:00:00",
            status="confirmed"
        )
        
        assert participant.booking_id == "booking-123"
        assert participant.event_id == "event-456"
        assert participant.user_id == "user-789"
        assert participant.user_email == "user@example.com"
        assert participant.event_name == "Test Event"
        assert participant.status == "confirmed"
    
    def test_participant_str_representation(self):
        """Test Participant __str__ method."""
        participant = Participant(
            booking_id="booking-123",
            event_id="event-456",
            user_id="user-789",
            user_email="user@example.com"
        )
        
        str_repr = str(participant)
        assert "booking-123" in str_repr
        assert "user@example.com" in str_repr
    
    @patch('data.database.SessionLocal')
    def test_get_session(self, mock_session_local):
        """Test getting a database session."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        
        session = get_session()
        
        assert session == mock_session
        mock_session_local.assert_called_once()
    
    def test_close_session(self):
        """Test closing a database session."""
        mock_session = Mock()
        
        close_session(mock_session)
        
        mock_session.close.assert_called_once()
    
    def test_participant_default_values(self):
        """Test Participant model can be created with minimal fields."""
        participant = Participant(
            booking_id="booking-123",
            event_id="event-456",
            user_id="user-789",
            user_email="user@example.com"
        )
        
        # Should be able to create participant with minimal fields
        assert participant.booking_id == "booking-123"
        assert participant.user_email == "user@example.com"
