"""
Unit tests for API routes.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from api.main import app


client = TestClient(app)


class TestAPIRoutes:
    """Test suite for API routes."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "notification-service"
    
    def test_send_notification_success(self):
        """Test successful notification sending."""
        payload = {
            "type": "event_created",
            "event": {
                "event_id": "event-123",
                "event_name": "Test Event",
                "description": "Test Description",
                "start_time": "2024-12-15T10:00:00",
                "end_time": "2024-12-15T12:00:00",
                "organizer_id": "organizer-1",
                "location": "Test Hall",
                "remaining_seats": 50
            }
        }
        
        response = client.post("/api/notifications/send", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["event_id"] == "event-123"
        assert "queued" in data["message"].lower()
    
    def test_send_notification_invalid_type(self):
        """Test notification with invalid type."""
        payload = {
            "type": "invalid_type",
            "event": {
                "event_id": "event-123",
                "event_name": "Test Event",
                "start_time": "2024-12-15T10:00:00",
                "end_time": "2024-12-15T12:00:00",
                "organizer_id": "organizer-1",
                "location": "Test Hall",
                "remaining_seats": 50
            }
        }
        
        response = client.post("/api/notifications/send", json=payload)
        
        assert response.status_code == 400
        assert "invalid type" in response.json()["detail"].lower()
    
    def test_send_notification_missing_fields(self):
        """Test notification with missing required fields."""
        payload = {
            "type": "event_created",
            "event": {
                "event_id": "event-123",
                "event_name": "Test Event"
                # Missing required fields
            }
        }
        
        response = client.post("/api/notifications/send", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_send_notification_all_types(self):
        """Test all valid notification types."""
        valid_types = ["event_created", "event_updated", "event_update", "event_cancelled", "event_reminder"]
        
        for notif_type in valid_types:
            payload = {
                "type": notif_type,
                "event": {
                    "event_id": "event-123",
                    "event_name": "Test Event",
                    "start_time": "2024-12-15T10:00:00",
                    "end_time": "2024-12-15T12:00:00",
                    "organizer_id": "organizer-1",
                    "location": "Test Hall",
                    "remaining_seats": 50
                }
            }
            
            response = client.post("/api/notifications/send", json=payload)
            
            assert response.status_code == 200, f"Failed for type: {notif_type}"
            assert response.json()["success"] is True
    
    def test_send_notification_with_reminder_type(self):
        """Test sending reminder notification."""
        payload = {
            "type": "event_reminder",
            "event": {
                "event_id": "event-123",
                "event_name": "Test Event",
                "start_time": "2024-12-15T10:00:00",
                "end_time": "2024-12-15T12:00:00",
                "organizer_id": "organizer-1",
                "location": "Test Hall",
                "remaining_seats": 50,
                "reminder_type": "one_day"
            }
        }
        
        response = client.post("/api/notifications/send", json=payload)
        
        assert response.status_code == 200
        assert response.json()["success"] is True
