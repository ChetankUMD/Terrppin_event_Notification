"""
Async email service for sending notifications.
Supports both SMTP (for local dev) and HTTP API providers (for production).
"""
import asyncio
import aiosmtplib
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class EmailProvider(ABC):
    """Abstract base class for email providers."""
    
    @abstractmethod
    async def send_email(
        self, 
        to: str, 
        subject: str, 
        body: str
    ) -> bool:
        """Send an email. Returns True if successful, False otherwise."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the provider for logging."""
        pass


class DummyEmailProvider(EmailProvider):
    """Dummy provider that logs emails without actually sending them."""
    
    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """Log email without sending."""
        logger.info(f"[DUMMY] Email sent to {to} | Subject: {subject}")
        # Simulate async operation
        await asyncio.sleep(0.01)
        return True
    
    def get_provider_name(self) -> str:
        return "Dummy (Testing Mode)"


class SMTPEmailProvider(EmailProvider):
    """SMTP-based email provider for local development."""
    
    def __init__(self, config):
        """Initialize SMTP provider with configuration."""
        self.config = config
    
    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email via SMTP."""
        try:
            message = self._create_message(to, subject, body)
            await self._send_smtp(message)
            logger.info(f"Email sent successfully to {to}")
            return True
        except Exception as e:
            logger.error(f"SMTP error: {type(e).__name__}: {e}")
            raise
    
    def _create_message(self, to: str, subject: str, body: str) -> MIMEMultipart:
        """Create MIME email message."""
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = f"{self.config.from_name} <{self.config.from_email}>"
        message['To'] = to
        
        # Attach HTML body
        html_part = MIMEText(body, 'html')
        message.attach(html_part)
        
        return message
    
    async def _send_smtp(self, message: MIMEMultipart):
        """Send email via SMTP."""
        # Determine security settings based on port
        use_tls = self.config.smtp_port == 465
        start_tls = self.config.smtp_port == 587
        
        # Use send_message helper which handles connection automatically
        await aiosmtplib.send(
            message,
            hostname=self.config.smtp_host,
            port=self.config.smtp_port,
            username=self.config.smtp_username,
            password=self.config.smtp_password,
            use_tls=use_tls,
            start_tls=start_tls,
            timeout=30
        )
    
    def get_provider_name(self) -> str:
        return f"SMTP ({self.config.smtp_host}:{self.config.smtp_port})"


class SendGridEmailProvider(EmailProvider):
    """SendGrid HTTP API-based email provider for production."""
    
    def __init__(self, config):
        """Initialize SendGrid provider with configuration."""
        self.config = config
        
        # Import SendGrid only when needed
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content
            self.SendGridAPIClient = SendGridAPIClient
            self.Mail = Mail
            self.Email = Email
            self.To = To
            self.Content = Content
        except ImportError:
            raise ImportError(
                "SendGrid library not installed. "
                "Install with: pip install sendgrid"
            )
        
        if not self.config.sendgrid_api_key:
            raise ValueError(
                "SENDGRID_API_KEY environment variable is required "
                "when using SendGrid provider"
            )
        
        self.client = self.SendGridAPIClient(self.config.sendgrid_api_key)
    
    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email via SendGrid HTTP API."""
        try:
            message = self.Mail(
                from_email=self.Email(
                    self.config.from_email, 
                    self.config.from_name
                ),
                to_emails=self.To(to),
                subject=subject,
                html_content=self.Content("text/html", body)
            )
            
            # SendGrid client is synchronous, run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.send(message)
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Email sent successfully to {to} via SendGrid")
                return True
            else:
                logger.error(
                    f"SendGrid API error: {response.status_code} - {response.body}"
                )
                raise Exception(f"SendGrid returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"SendGrid error: {type(e).__name__}: {e}")
            raise
    
    def get_provider_name(self) -> str:
        return "SendGrid (HTTP API)"


class EmailService:
    """Async email service with support for multiple providers."""
    
    def __init__(self):
        """Initialize email service with appropriate provider."""
        self.config = settings.email
        self.provider = self._create_provider()
        
        logger.info(
            f"Email service initialized with provider: "
            f"{self.provider.get_provider_name()}"
        )
    
    def _create_provider(self) -> EmailProvider:
        """Create the appropriate email provider based on configuration."""
        # Dummy mode overrides provider selection
        if self.config.dummy_mode:
            return DummyEmailProvider()
        
        # Select provider based on configuration
        if self.config.provider == 'sendgrid':
            return SendGridEmailProvider(self.config)
        elif self.config.provider == 'smtp':
            return SMTPEmailProvider(self.config)
        else:
            raise ValueError(
                f"Unknown email provider: {self.config.provider}. "
                f"Valid options: 'smtp', 'sendgrid'"
            )
    
    async def send_email(
        self, 
        to: str, 
        subject: str, 
        body: str,
        retry_count: int = 0
    ) -> bool:
        """
        Send an email asynchronously.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (HTML supported)
            retry_count: Current retry attempt (for internal use)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            return await self.provider.send_email(to, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            
            # Retry logic
            if retry_count < settings.processor.max_retries:
                retry_count += 1
                logger.info(
                    f"Retrying email to {to} "
                    f"(attempt {retry_count}/{settings.processor.max_retries})"
                )
                await asyncio.sleep(settings.processor.retry_delay)
                return await self.send_email(to, subject, body, retry_count)
            
            logger.error(
                f"Failed to send email to {to} after "
                f"{settings.processor.max_retries} retries"
            )
            return False
    
    async def send_batch(
        self, 
        emails: list[tuple[str, str, str]]
    ) -> tuple[int, int]:
        """
        Send multiple emails concurrently.
        
        Args:
            emails: List of tuples (to, subject, body)
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        tasks = [
            self.send_email(to, subject, body)
            for to, subject, body in emails
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if r is True)
        failed = len(results) - successful
        
        logger.info(
            f"Batch email results: {successful} successful, {failed} failed"
        )
        
        return successful, failed
