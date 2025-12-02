"""
Unit tests for EmailService.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from email_service.email_service import EmailService


class TestEmailService:
    """Test suite for EmailService."""
    
    @pytest.fixture
    def email_service(self):
        """Create an EmailService instance."""
        with patch('email_service.email_service.settings') as mock_settings:
            mock_settings.email.dummy_mode = False
            mock_settings.email.smtp_host = "smtp.example.com"
            mock_settings.email.smtp_port = 587
            mock_settings.email.smtp_username = "user@example.com"
            mock_settings.email.smtp_password = "password"
            mock_settings.email.from_name = "Test Service"
            mock_settings.email.from_email = "noreply@example.com"
            mock_settings.processor.max_retries = 3
            mock_settings.processor.retry_delay = 1
            return EmailService()
    
    @pytest.fixture
    def dummy_email_service(self):
        """Create an EmailService instance in dummy mode."""
        with patch('email_service.email_service.settings') as mock_settings:
            mock_settings.email.dummy_mode = True
            return EmailService()
    
    @pytest.mark.asyncio
    async def test_dummy_mode_send_email(self, dummy_email_service):
        """Test that dummy mode logs emails instead of sending them."""
        result = await dummy_email_service.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="<p>Test Body</p>"
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_email_success(self, email_service):
        """Test successful email sending."""
        with patch('email_service.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = None
            
            result = await email_service.send_email(
                to="recipient@example.com",
                subject="Test Subject",
                body="<p>Test Body</p>"
            )
            
            assert result is True
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_with_retry(self, email_service):
        """Test email sending with retry on failure."""
        with patch('email_service.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            # Fail twice, then succeed
            mock_send.side_effect = [
                Exception("Connection failed"),
                Exception("Connection failed"),
                None
            ]
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await email_service.send_email(
                    to="recipient@example.com",
                    subject="Test Subject",
                    body="<p>Test Body</p>"
                )
            
            assert result is True
            assert mock_send.call_count == 3
    
    @pytest.mark.asyncio
    async def test_send_email_max_retries_exceeded(self, email_service):
        """Test email sending fails after max retries."""
        with patch('email_service.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("Connection failed")
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await email_service.send_email(
                    to="recipient@example.com",
                    subject="Test Subject",
                    body="<p>Test Body</p>"
                )
            
            assert result is False
            # Initial + 3 retries = 4 total attempts
            assert mock_send.call_count == 4
    
    @pytest.mark.asyncio
    async def test_create_message(self, email_service):
        """Test MIME message creation."""
        message = email_service._create_message(
            to="recipient@example.com",
            subject="Test Subject",
            body="<p>Test Body</p>"
        )
        
        assert message['Subject'] == "Test Subject"
        assert message['To'] == "recipient@example.com"
        assert "noreply@example.com" in message['From']
    
    @pytest.mark.asyncio
    async def test_smtp_send_port_587(self, email_service):
        """Test SMTP send with port 587 (STARTTLS)."""
        with patch('email_service.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            message = email_service._create_message(
                to="test@example.com",
                subject="Test",
                body="<p>Body</p>"
            )
            
            await email_service._send_smtp(message)
            
            # Verify the call was made with the right parameters
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs['hostname'] == "smtp.example.com"
            assert call_kwargs['port'] == 587
            assert call_kwargs['start_tls'] is True
            assert call_kwargs['use_tls'] is False
    
    @pytest.mark.asyncio
    async def test_smtp_send_port_465(self, email_service):
        """Test SMTP send with port 465 (SSL/TLS)."""
        email_service.config.smtp_port = 465
        
        with patch('email_service.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            message = email_service._create_message(
                to="test@example.com",
                subject="Test",
                body="<p>Body</p>"
            )
            
            await email_service._send_smtp(message)
            
            # Verify the call was made with the right parameters
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs['use_tls'] is True
            assert call_kwargs['start_tls'] is False
    
    @pytest.mark.asyncio
    async def test_send_batch_success(self, email_service):
        """Test batch email sending."""
        with patch('email_service.email_service.aiosmtplib.send', new_callable=AsyncMock):
            emails = [
                ("user1@example.com", "Subject 1", "<p>Body 1</p>"),
                ("user2@example.com", "Subject 2", "<p>Body 2</p>"),
                ("user3@example.com", "Subject 3", "<p>Body 3</p>")
            ]
            
            successful, failed = await email_service.send_batch(emails)
            
            assert successful == 3
            assert failed == 0
    
    @pytest.mark.asyncio
    async def test_send_batch_partial_failure(self, email_service):
        """Test batch email sending with partial failures."""
        with patch.object(email_service, 'send_email', new_callable=AsyncMock) as mock_send:
            # First succeeds, second fails, third succeeds
            mock_send.side_effect = [True, False, True]
            
            emails = [
                ("user1@example.com", "Subject 1", "<p>Body 1</p>"),
                ("user2@example.com", "Subject 2", "<p>Body 2</p>"),
                ("user3@example.com", "Subject 3", "<p>Body 3</p>")
            ]
            
            successful, failed = await email_service.send_batch(emails)
            
            assert successful == 2
            assert failed == 1
