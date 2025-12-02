"""
Unit tests for EmailService with provider support.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from email_service.email_service import (
    EmailService, 
    DummyEmailProvider, 
    SMTPEmailProvider,
    SendGridEmailProvider
)


class TestDummyEmailProvider:
    """Test suite for DummyEmailProvider."""
    
    @pytest.mark.asyncio
    async def test_dummy_send_email(self):
        """Test that dummy provider logs emails."""
        provider = DummyEmailProvider()
        
        result = await provider.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="<p>Test Body</p>"
        )
        
        assert result is True
        assert provider.get_provider_name() == "Dummy (Testing Mode)"


class TestSMTPEmailProvider:
    """Test suite for SMTPEmailProvider."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock email configuration."""
        config = Mock()
        config.smtp_host = "smtp.example.com"
        config.smtp_port = 587
        config.smtp_username = "user@example.com"
        config.smtp_password = "password"
        config.from_name = "Test Service"
        config.from_email = "noreply@example.com"
        return config
    
    @pytest.mark.asyncio
    async def test_smtp_send_email_success(self, mock_config):
        """Test successful email sending via SMTP."""
        provider = SMTPEmailProvider(mock_config)
        
        with patch('email_service.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = None
            
            result = await provider.send_email(
                to="recipient@example.com",
                subject="Test Subject",
                body="<p>Test Body</p>"
            )
            
            assert result is True
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_smtp_send_port_587(self, mock_config):
        """Test SMTP send with port 587 (STARTTLS)."""
        provider = SMTPEmailProvider(mock_config)
        
        with patch('email_service.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            await provider.send_email(
                to="test@example.com",
                subject="Test",
                body="<p>Body</p>"
            )
            
            # Verify the call was made with the right parameters
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs['hostname'] == "smtp.example.com"
            assert call_kwargs['port'] == 587
            assert call_kwargs['start_tls'] is True
            assert call_kwargs['use_tls'] is False
    
    @pytest.mark.asyncio
    async def test_smtp_send_port_465(self, mock_config):
        """Test SMTP send with port 465 (SSL/TLS)."""
        mock_config.smtp_port = 465
        provider = SMTPEmailProvider(mock_config)
        
        with patch('email_service.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            await provider.send_email(
                to="test@example.com",
                subject="Test",
                body="<p>Body</p>"
            )
            
            # Verify the call was made with the right parameters
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs['use_tls'] is True
            assert call_kwargs['start_tls'] is False
    
    def test_get_provider_name(self, mock_config):
        """Test provider name."""
        provider = SMTPEmailProvider(mock_config)
        assert provider.get_provider_name() == "SMTP (smtp.example.com:587)"


class TestSendGridEmailProvider:
    """Test suite for SendGridEmailProvider."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock email configuration with SendGrid API key."""
        config = Mock()
        config.sendgrid_api_key = "test_api_key"
        config.from_name = "Test Service"
        config.from_email = "noreply@example.com"
        return config
    
    @pytest.mark.asyncio
    async def test_sendgrid_send_email_success(self, mock_config):
        """Test successful email sending via SendGrid."""
        with patch('sendgrid.SendGridAPIClient') as mock_sg_client, \
             patch('sendgrid.helpers.mail.Mail') as mock_mail:
            # Mock the SendGrid response
            mock_response = Mock()
            mock_response.status_code = 202
            mock_client_instance = Mock()
            mock_client_instance.send.return_value = mock_response
            mock_sg_client.return_value = mock_client_instance
            
            provider = SendGridEmailProvider(mock_config)
            
            result = await provider.send_email(
                to="recipient@example.com",
                subject="Test Subject",
                body="<p>Test Body</p>"
            )
            
            assert result is True
            mock_client_instance.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sendgrid_send_email_failure(self, mock_config):
        """Test failed email sending via SendGrid."""
        with patch('sendgrid.SendGridAPIClient') as mock_sg_client, \
             patch('sendgrid.helpers.mail.Mail') as mock_mail:
            # Mock a failed SendGrid response
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.body = "Bad Request"
            mock_client_instance = Mock()
            mock_client_instance.send.return_value = mock_response
            mock_sg_client.return_value = mock_client_instance
            
            provider = SendGridEmailProvider(mock_config)
            
            with pytest.raises(Exception):
                await provider.send_email(
                    to="recipient@example.com",
                    subject="Test Subject",
                    body="<p>Test Body</p>"
                )
    
    def test_sendgrid_missing_api_key(self):
        """Test SendGridEmailProvider raises error when API key is missing."""
        config = Mock()
        config.sendgrid_api_key = ""
        
        with pytest.raises(ValueError, match="SENDGRID_API_KEY"):
            SendGridEmailProvider(config)
    
    def test_get_provider_name(self, mock_config):
        """Test provider name."""
        with patch('sendgrid.SendGridAPIClient'), \
             patch('sendgrid.helpers.mail.Mail'):
            provider = SendGridEmailProvider(mock_config)
            assert provider.get_provider_name() == "SendGrid (HTTP API)"


class TestEmailService:
    """Test suite for EmailService."""
    
    @pytest.fixture
    def smtp_email_service(self):
        """Create an EmailService instance with SMTP provider."""
        with patch('email_service.email_service.settings') as mock_settings:
            mock_settings.email.dummy_mode = False
            mock_settings.email.provider = 'smtp'
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
            mock_settings.email.provider = 'smtp'
            return EmailService()
    
    @pytest.fixture
    def sendgrid_email_service(self):
        """Create an EmailService instance with SendGrid provider."""
        with patch('email_service.email_service.settings') as mock_settings:
            mock_settings.email.dummy_mode = False
            mock_settings.email.provider = 'sendgrid'
            mock_settings.email.sendgrid_api_key = "test_api_key"
            mock_settings.email.from_name = "Test Service"
            mock_settings.email.from_email = "noreply@example.com"
            mock_settings.processor.max_retries = 3
            mock_settings.processor.retry_delay = 1
            
            with patch('sendgrid.SendGridAPIClient'), \
                 patch('sendgrid.helpers.mail.Mail'):
                return EmailService()
    
    def test_create_dummy_provider(self, dummy_email_service):
        """Test that dummy mode creates DummyEmailProvider."""
        assert isinstance(dummy_email_service.provider, DummyEmailProvider)
    
    def test_create_smtp_provider(self, smtp_email_service):
        """Test that SMTP provider is created correctly."""
        assert isinstance(smtp_email_service.provider, SMTPEmailProvider)
    
    def test_create_sendgrid_provider(self, sendgrid_email_service):
        """Test that SendGrid provider is created correctly."""
        assert isinstance(sendgrid_email_service.provider, SendGridEmailProvider)
    
    def test_invalid_provider(self):
        """Test that invalid provider raises ValueError."""
        with patch('email_service.email_service.settings') as mock_settings:
            mock_settings.email.dummy_mode = False
            mock_settings.email.provider = 'invalid'
            
            with pytest.raises(ValueError, match="Unknown email provider"):
                EmailService()
    
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
    async def test_send_email_success(self, smtp_email_service):
        """Test successful email sending."""
        with patch('email_service.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = None
            
            result = await smtp_email_service.send_email(
                to="recipient@example.com",
                subject="Test Subject",
                body="<p>Test Body</p>"
            )
            
            assert result is True
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_with_retry(self, smtp_email_service):
        """Test email sending with retry on failure."""
        with patch('email_service.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            # Fail twice, then succeed
            mock_send.side_effect = [
                Exception("Connection failed"),
                Exception("Connection failed"),
                None
            ]
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await smtp_email_service.send_email(
                    to="recipient@example.com",
                    subject="Test Subject",
                    body="<p>Test Body</p>"
                )
            
            assert result is True
            assert mock_send.call_count == 3
    
    @pytest.mark.asyncio
    async def test_send_email_max_retries_exceeded(self, smtp_email_service):
        """Test email sending fails after max retries."""
        with patch('email_service.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("Connection failed")
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await smtp_email_service.send_email(
                    to="recipient@example.com",
                    subject="Test Subject",
                    body="<p>Test Body</p>"
                )
            
            assert result is False
            # Initial + 3 retries = 4 total attempts
            assert mock_send.call_count == 4
    
    @pytest.mark.asyncio
    async def test_send_batch_success(self, smtp_email_service):
        """Test batch email sending."""
        with patch('email_service.email_service.aiosmtplib.send', new_callable=AsyncMock):
            emails = [
                ("user1@example.com", "Subject 1", "<p>Body 1</p>"),
                ("user2@example.com", "Subject 2", "<p>Body 2</p>"),
                ("user3@example.com", "Subject 3", "<p>Body 3</p>")
            ]
            
            successful, failed = await smtp_email_service.send_batch(emails)
            
            assert successful == 3
            assert failed == 0
    
    @pytest.mark.asyncio
    async def test_send_batch_partial_failure(self, smtp_email_service):
        """Test batch email sending with partial failures."""
        with patch.object(smtp_email_service, 'send_email', new_callable=AsyncMock) as mock_send:
            # First succeeds, second fails, third succeeds
            mock_send.side_effect = [True, False, True]
            
            emails = [
                ("user1@example.com", "Subject 1", "<p>Body 1</p>"),
                ("user2@example.com", "Subject 2", "<p>Body 2</p>"),
                ("user3@example.com", "Subject 3", "<p>Body 3</p>")
            ]
            
            successful, failed = await smtp_email_service.send_batch(emails)
            
            assert successful == 2
            assert failed == 1
    
    @pytest.mark.asyncio
    async def test_sendgrid_send_email_success(self, sendgrid_email_service):
        """Test successful email sending via SendGrid."""
        with patch('sendgrid.SendGridAPIClient') as mock_sg_client, \
             patch('sendgrid.helpers.mail.Mail') as mock_mail:
            # Mock the SendGrid response
            mock_response = Mock()
            mock_response.status_code = 202
            mock_client_instance = Mock()
            mock_client_instance.send.return_value = mock_response
            mock_sg_client.return_value = mock_client_instance
            
            # Recreate service to use the mocked client
            with patch('email_service.email_service.settings') as mock_settings:
                mock_settings.email.dummy_mode = False
                mock_settings.email.provider = 'sendgrid'
                mock_settings.email.sendgrid_api_key = "test_api_key"
                mock_settings.email.from_name = "Test Service"
                mock_settings.email.from_email = "noreply@example.com"
                mock_settings.processor.max_retries = 3
                
                service = EmailService()
                result = await service.send_email(
                    to="recipient@example.com",
                    subject="Test Subject",
                    body="<p>Test Body</p>"
                )
                
                assert result is True
