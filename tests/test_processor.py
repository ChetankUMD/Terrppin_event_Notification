"""
Unit tests for NotificationProcessor.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from processor.notification_processor import NotificationProcessor
from models.dto import NotificationMessage, Event


class TestNotificationProcessor:
    """Test suite for NotificationProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create a NotificationProcessor instance."""
        return NotificationProcessor()
    
    @pytest.fixture
    def sample_event(self):
        """Create a sample event."""
        return Event(
            event_id="event-123",
            event_name="Test Event",
            description="A test event",
            start_time="2024-12-15T10:00:00",
            end_time="2024-12-15T12:00:00",
            organizer_id="organizer-1",
            location="Test Hall",
            remaining_seats=50
        )
    
    @pytest.mark.asyncio
    async def test_process_event_created(self, processor, sample_event):
        """Test processing event_created notification."""
        message = NotificationMessage(
            type="event_created",
            event=sample_event
        )
        
        with patch('processor.notification_processor.ParticipantRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo.__enter__ = Mock(return_value=mock_repo)
            mock_repo.__exit__ = Mock(return_value=None)
            mock_repo.count_participants_by_event.return_value = 0
            mock_repo_class.return_value = mock_repo
            
            await processor.process(message)
            
            mock_repo.count_participants_by_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_unknown_type(self, processor, sample_event):
        """Test processing unknown notification type."""
        message = NotificationMessage(
            type="unknown_type",
            event=sample_event
        )
        
        # Should handle gracefully
        with patch('processor.notification_processor.ParticipantRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo.__enter__ = Mock(return_value=mock_repo)
            mock_repo.__exit__ = Mock(return_value=None)
            mock_repo_class.return_value = mock_repo
            
            await processor.process(message)
    
    @pytest.mark.asyncio
    async def test_process_with_participants(self, processor, sample_event):
        """Test processing with actual participants."""
        message = NotificationMessage(
            type="event_created",
            event=sample_event
        )
        
        mock_participant = Mock()
        mock_participant.name = "Test User"
        mock_participant.email = "test@example.com"
        
        with patch('processor.notification_processor.ParticipantRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo.__enter__ = Mock(return_value=mock_repo)
            mock_repo.__exit__ = Mock(return_value=None)
            mock_repo.count_participants_by_event.return_value = 1
            mock_repo.get_participants_by_event.side_effect = [[mock_participant], []]
            mock_repo_class.return_value = mock_repo
            
            with patch.object(processor.email_service, 'send_batch', new_callable=AsyncMock, return_value=(1, 0)):
                await processor.process(message)
            
            # Verify participants were fetched
            assert mock_repo.get_participants_by_event.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_send_batch_emails(self, processor, sample_event):
        """Test sending batch emails."""
        mock_participant1 = Mock()
        mock_participant1.name = "User 1"
        mock_participant1.email = "user1@example.com"
        
        mock_participant2 = Mock()
        mock_participant2.name = "User 2"
        mock_participant2.email = "user2@example.com"
        
        participants = [mock_participant1, mock_participant2]
        
        with patch.object(processor.email_service, 'send_batch', new_callable=AsyncMock, return_value=(2, 0)) as mock_send:
            successful, failed = await processor._send_batch_emails(
                participants=participants,
                event_type='event_created',
                event=sample_event,
                batch_number=1
            )
            
            assert successful == 2
            assert failed == 0
            mock_send.assert_called_once()
            
            # Verify email tasks were created correctly
            email_tasks = mock_send.call_args[0][0]
            assert len(email_tasks) == 2
            assert email_tasks[0][0] == "user1@example.com"
            assert email_tasks[1][0] == "user2@example.com"
