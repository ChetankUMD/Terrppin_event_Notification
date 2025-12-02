"""
Unit tests for ParticipantRepository.
"""
import pytest
from unittest.mock import Mock, patch
from data.repository import ParticipantRepository
from models.dto import BookingBatchResponse


class TestParticipantRepository:
    """Test suite for ParticipantRepository."""
    
    @pytest.fixture
    def mock_booking_client(self):
        """Create a mock BookingAPIClient."""
        return Mock()
    
    @pytest.fixture
    def repository(self, mock_booking_client):
        """Create a repository with mocked client."""
        return ParticipantRepository(booking_client=mock_booking_client)
    
    def test_repository_initialization(self):
        """Test that repository initializes with a BookingAPIClient."""
        repo = ParticipantRepository()
        assert hasattr(repo, 'booking_client')
        assert repo.booking_client is not None
    
    def test_get_participants_by_event_success(self, repository, mock_booking_client):
        """Test successful participant retrieval."""
        # Mock booking data
        mock_bookings = [
            BookingBatchResponse(
                booking_id="booking-1",
                event_id="event-123",
                user_id="user-1",
                user_email="user1@example.com",
                event_name="Test Event",
                status="confirmed"
            ),
            BookingBatchResponse(
                booking_id="booking-2",
                event_id="event-123",
                user_id="user-2",
                user_email="user2@example.com",
                event_name="Test Event",
                status="confirmed"
            )
        ]
        mock_booking_client.get_bookings_batch.return_value = mock_bookings
        
        # Execute
        participants = repository.get_participants_by_event(
            event_id="event-123",
            offset=0,
            limit=10
        )
        
        # Assert
        assert len(participants) == 2
        assert participants[0].user_email == "user1@example.com"
        assert participants[1].user_email == "user2@example.com"
        
        mock_booking_client.get_bookings_batch.assert_called_once_with(
            event_id="event-123",
            offset=0,
            batch_size=10
        )
    
    def test_get_participants_by_event_empty_result(self, repository, mock_booking_client):
        """Test participant retrieval with no results."""
        mock_booking_client.get_bookings_batch.return_value = []
        
        # Execute
        participants = repository.get_participants_by_event(
            event_id="event-123",
            offset=0,
            limit=10
        )
        
        # Assert
        assert participants == []
    
    def test_get_participants_by_event_with_pagination(self, repository, mock_booking_client):
        """Test participant retrieval with pagination parameters."""
        mock_booking_client.get_bookings_batch.return_value = []
        
        # Execute
        repository.get_participants_by_event(
            event_id="event-456",
            offset=50,
            limit=25
        )
        
        # Assert - verify pagination params are passed correctly
        mock_booking_client.get_bookings_batch.assert_called_once_with(
            event_id="event-456",
            offset=50,
            batch_size=25
        )
    
    def test_count_participants_by_event_success(self, repository, mock_booking_client):
        """Test successful participant count retrieval."""
        mock_booking_client.get_bookings_count.return_value = 42
        
        # Execute
        count = repository.count_participants_by_event("event-123")
        
        # Assert
        assert count == 42
        mock_booking_client.get_bookings_count.assert_called_once_with("event-123")
    
    def test_count_participants_by_event_zero(self, repository, mock_booking_client):
        """Test participant count when no participants exist."""
        mock_booking_client.get_bookings_count.return_value = 0
        
        # Execute
        count = repository.count_participants_by_event("event-empty")
        
        # Assert
        assert count == 0
    
    def test_get_participants_api_error_propagates(self, repository, mock_booking_client):
        """Test that API errors are propagated."""
        mock_booking_client.get_bookings_batch.side_effect = Exception("API Error")
        
        # Execute and assert
        with pytest.raises(Exception, match="API Error"):
            repository.get_participants_by_event("event-123")
    
    def test_count_participants_api_error_propagates(self, repository, mock_booking_client):
        """Test that API errors are propagated for count."""
        mock_booking_client.get_bookings_count.side_effect = Exception("API Error")
        
        # Execute and assert
        with pytest.raises(Exception, match="API Error"):
            repository.count_participants_by_event("event-123")
    
    def test_context_manager_support(self, mock_booking_client):
        """Test that repository supports context manager protocol."""
        with ParticipantRepository(booking_client=mock_booking_client) as repo:
            assert repo is not None
            assert hasattr(repo, 'booking_client')
    
    def test_close_method(self, repository):
        """Test that close method exists and can be called."""
        # Should not raise any errors
        repository.close()
    
    def test_add_participant(self):
        """Test adding a participant to the database."""
        with patch('data.repository.get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            
            repo = ParticipantRepository()
            
            participant = repo.add_participant(
                booking_id="booking-123",
                event_id="event-456",
                user_id="user-789",
                user_email="user@example.com",
                event_name="Test Event",
                booking_time="2024-12-01T10:00:00",
                status="confirmed"
            )
            
            assert participant is not None
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
    
    def test_add_participant_rollback_on_error(self):
        """Test that session rolls back on error during add_participant."""
        with patch('data.repository.get_session') as mock_get_session:
            mock_session = Mock()
            mock_session.commit.side_effect = Exception("Database error")
            mock_get_session.return_value = mock_session
            
            repo = ParticipantRepository()
            
            with pytest.raises(Exception, match="Database error"):
                repo.add_participant(
                    booking_id="booking-123",
                    event_id="event-456",
                    user_id="user-789",
                    user_email="user@example.com"
                )
            
            mock_session.rollback.assert_called_once()
    
    def test_add_participants_from_bookings(self):
        """Test bulk adding participants from booking data."""
        with patch('data.repository.get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            
            repo = ParticipantRepository()
            
            bookings = [
                {
                    "booking_id": "booking-1",
                    "event_id": "event-123",
                    "user_id": "user-1",
                    "user_email": "user1@example.com",
                    "event_name": "Event 1",
                    "status": "confirmed"
                },
                {
                    "booking_id": "booking-2",
                    "event_id": "event-123",
                    "user_id": "user-2",
                    "user_email": "user2@example.com",
                    "event_name": "Event 1",
                    "status": "confirmed"
                }
            ]
            
            count = repo.add_participants_from_bookings(bookings)
            
            assert count == 2
            assert mock_session.add.call_count == 2
            assert mock_session.commit.call_count == 2
    
    def test_add_participants_from_bookings_partial_failure(self):
        """Test that bulk add continues on individual failures."""
        with patch('data.repository.get_session') as mock_get_session:
            mock_session = Mock()
            # First commit succeeds, second fails, third succeeds
            mock_session.commit.side_effect = [None, Exception("Error"), None]
            mock_get_session.return_value = mock_session
            
            repo = ParticipantRepository()
            
            bookings = [
                {
                    "booking_id": "booking-1",
                    "event_id": "event-123",
                    "user_id": "user-1",
                    "user_email": "user1@example.com"
                },
                {
                    "booking_id": "booking-2",
                    "event_id": "event-123",
                    "user_id": "user-2",
                    "user_email": "user2@example.com"
                },
                {
                    "booking_id": "booking-3",
                    "event_id": "event-123",
                    "user_id": "user-3",
                    "user_email": "user3@example.com"
                }
            ]
            
            count = repo.add_participants_from_bookings(bookings)
            
            # Should have added 2 successfully (first and third)
            assert count == 2
