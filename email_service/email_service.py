"""
Async email service for sending notifications.
"""
import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Async email service with SMTP support and dummy mode for testing."""
    
    def __init__(self):
        """Initialize email service with configuration."""
        self.config = settings.email
        self.dummy_mode = self.config.dummy_mode
        
        if self.dummy_mode:
            logger.info("Email service initialized in DUMMY MODE (no emails will be sent)")
        else:
            logger.info(
                f"Email service initialized with SMTP: "
                f"{self.config.smtp_host}:{self.config.smtp_port}"
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
            if self.dummy_mode:
                # Dummy mode: just log the email
                logger.info(
                    f"[DUMMY] Email sent to {to} | Subject: {subject}"
                )
                # Simulate async operation
                await asyncio.sleep(0.01)
                return True
            
            # Real SMTP sending
            message = self._create_message(to, subject, body)
            
            await self._send_smtp(message)
            
            logger.info(f"Email sent successfully to {to}")
            return True
            
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
    
    def _create_message(self, to: str, subject: str, body: str) -> MIMEMultipart:
        """
        Create MIME email message.
        
        Args:
            to: Recipient email
            subject: Email subject
            body: Email body (HTML)
            
        Returns:
            MIMEMultipart message
        """
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = f"{self.config.from_name} <{self.config.from_email}>"
        message['To'] = to
        
        # Attach HTML body
        html_part = MIMEText(body, 'html')
        message.attach(html_part)
        
        return message
    
    async def _send_smtp(self, message: MIMEMultipart):
        """
        Send email via SMTP.
        
        Args:
            message: MIME message to send
            
        Raises:
            Exception: If SMTP sending fails
        """
        try:
            # Use send_message helper which handles connection automatically
            await aiosmtplib.send(
                message,
                hostname=self.config.smtp_host,
                port=self.config.smtp_port,
                username=self.config.smtp_username,
                password=self.config.smtp_password,
                start_tls=True if self.config.smtp_port == 587 else False,
                timeout=30
            )
        except Exception as e:
            logger.error(f"SMTP error: {type(e).__name__}: {e}")
            raise
    
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
