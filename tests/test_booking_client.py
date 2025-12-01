"""
Unit tests for BookingAPIClient.
"""
import pytest
from unittest.mock import Mock, patch
import httpx
from api.booking_client import BookingAPIClient
from models.dto import BookingBatchResponse


class TestBookingAPIClient:
    """Test suite for BookingAPIClient."""
    
    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return BookingAPIClient(base_url="http://test-api:8000", timeout=10)
    
    def test_client_initialization(self, client):
        """Test that client initializes with correct configuration."""
        assert client.base_url == "http://test-api:8000"
        assert client.timeout == 10
    
    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base URL."""
        client = BookingAPIClient(base_url="http://test-api:8000/")
        assert client.base_url == "http://test-api:8000"
    
    @patch('httpx.Client')
    def test_get_bookings_count_success(self, mock_httpx_client, client):
        """Test successful booking count retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "event_id": "test-event-123",
            "total_bookings": 42
        }
        
        # Setup mock client
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_context)
        mock_context.__exit__ = Mock(return_value=None)
        mock_context.get = Mock(return_value=mock_response)
        mock_httpx_client.return_value = mock_context
        
        # Execute
        count = client.get_bookings_count("test-event-123")
        
        # Assert
        assert count == 42
        mock_context.get.assert_called_once_with(
            "http://test-api:8000/bookings/count",
            params={"event_id": "test-event-123"}
        )
    
    @patch('httpx.Client')
    def test_get_bookings_count_empty_response(self, mock_httpx_client, client):
        """Test booking count with empty response."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        
        # Setup mock client
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_context)
        mock_context.__exit__ = Mock(return_value=None)
        mock_context.get = Mock(return_value=mock_response)
        mock_httpx_client.return_value = mock_context
        
        # Execute
        count = client.get_bookings_count("test-event-123")
        
        # Assert - should default to 0
        assert count == 0
    
    @patch('httpx.Client')
    def test_get_bookings_batch_success(self, mock_httpx_client, client):
        """Test successful booking batch retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "booking_id": "booking-1",
                "event_id": "event-123",
                "user_id": "user-1",
                "user_email": "user1@example.com",
                "event_name": "Test Event",
                "booking_time": "2025-11-30T10:00:00",
                "status": "confirmed"
            },
            {
                "booking_id": "booking-2",
                "event_id": "event-123",
                "user_id": "user-2",
                "user_email": "user2@example.com",
                "event_name": "Test Event",
                "booking_time": "2025-11-30T11:00:00",
                "status": "confirmed"
            }
        ]
        
        # Setup mock client
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_context)
        mock_context.__exit__ = Mock(return_value=None)
        mock_context.get = Mock(return_value=mock_response)
        mock_httpx_client.return_value = mock_context
        
        # Execute
        bookings = client.get_bookings_batch("event-123", offset=0, batch_size=10)
        
        # Assert
        assert len(bookings) == 2
        assert all(isinstance(b, BookingBatchResponse) for b in bookings)
        assert bookings[0].booking_id == "booking-1"
        assert bookings[0].user_email == "user1@example.com"
        assert bookings[1].booking_id == "booking-2"
        
        mock_context.get.assert_called_once_with(
            "http://test-api:8000/bookings/batch",
            params={"event_id": "event-123", "offset": 0, "batch_size": 10}
        )
    
    @patch('httpx.Client')
    def test_get_bookings_batch_404_returns_empty_list(self, mock_httpx_client, client):
        """Test that 404 response returns empty list (no more results)."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        
        # Setup mock client
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_context)
        mock_context.__exit__ = Mock(return_value=None)
        mock_context.get = Mock(return_value=mock_response)
        mock_httpx_client.return_value = mock_context
        
        # Execute
        bookings = client.get_bookings_batch("event-123", offset=100, batch_size=10)
        
        # Assert - should return empty list, not raise exception
        assert bookings == []
    
    @patch('httpx.Client')
    def test_get_bookings_batch_empty_response(self, mock_httpx_client, client):
        """Test booking batch with empty array response."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        # Setup mock client
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_context)
        mock_context.__exit__ = Mock(return_value=None)
        mock_context.get = Mock(return_value=mock_response)
        mock_httpx_client.return_value = mock_context
        
        # Execute
        bookings = client.get_bookings_batch("event-123", offset=0, batch_size=10)
        
        # Assert
        assert bookings == []
    
    @patch('httpx.Client')
    def test_get_bookings_count_http_error(self, mock_httpx_client, client):
        """Test HTTP error handling for count endpoint."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=Mock(), response=mock_response
        )
        
        # Setup mock client
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_context)
        mock_context.__exit__ = Mock(return_value=None)
        mock_context.get = Mock(return_value=mock_response)
        mock_httpx_client.return_value = mock_context
        
        # Execute and assert
        with pytest.raises(httpx.HTTPStatusError):
            client.get_bookings_count("event-123")
    
    @patch('httpx.Client')
    def test_get_bookings_batch_http_error(self, mock_httpx_client, client):
        """Test HTTP error handling for batch endpoint (non-404)."""
        # Mock error response (500, not 404)
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=Mock(), response=mock_response
        )
        
        # Setup mock client
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_context)
        mock_context.__exit__ = Mock(return_value=None)
        mock_context.get = Mock(return_value=mock_response)
        mock_httpx_client.return_value = mock_context
        
        # Execute and assert - should raise for non-404 errors
        with pytest.raises(httpx.HTTPStatusError):
            client.get_bookings_batch("event-123", offset=0, batch_size=10)
