"""
Notification processor for handling event notification messages.
"""
import asyncio
from models.dto import NotificationMessage
from data.repository import ParticipantRepository
from email_service.email_service import EmailService
from templates.email_templates import EmailTemplateLoader
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class NotificationProcessor:
    """Processes notification messages and sends emails to participants."""
    
    def __init__(self):
        """Initialize notification processor."""
        self.email_service = EmailService()
        self.batch_size = settings.processor.batch_size
        logger.info(
            f"NotificationProcessor initialized with batch_size={self.batch_size}"
        )
    
    async def process(self, message: NotificationMessage):
        """
        Process a notification message.
        
        Steps:
        1. Extract type and event from message
        2. Load email template by type
        3. Fetch participants from database in batches
        4. Send email to all participants until all processed
        
        Args:
            message: NotificationMessage DTO
        """
        logger.info(f"Processing message: {message}")
        
        # Step 1: Extract type and event
        event_type = message.type
        event = message.event
        
        logger.info(
            f"Step 1: Extracted event_type={event_type}, "
            f"event_id={event.event_id}, event_name={event.event_name}"
        )
        
        # Step 2: Load email template by type
        try:
            template = EmailTemplateLoader.get_template(event_type)
            logger.info(f"Step 2: Loaded template for event_type={event_type}")
        except ValueError as e:
            logger.error(f"Failed to load template: {e}")
            return
        
        # Step 3 & 4: Fetch participants in batches and send emails
        with ParticipantRepository() as repo:
            # Get total count for logging
            # Note: Using event_id as string now (UUID format)
            total_participants = repo.count_participants_by_event(event.event_id)
            logger.info(
                f"Step 3: Total participants to process: {total_participants}"
            )
            
            if total_participants == 0:
                logger.warning(
                    f"No participants found for event_id={event.event_id}"
                )
                return
            
            offset = 0
            batch_number = 1
            total_sent = 0
            total_failed = 0
            
            while True:
                # Fetch batch of participants
                participants = repo.get_participants_by_event(
                    event_id=event.event_id,
                    offset=offset,
                    limit=self.batch_size
                )
                
                if not participants:
                    logger.info("No more participants to process")
                    break
                
                logger.info(
                    f"Step 4: Processing batch {batch_number} "
                    f"({len(participants)} participants, offset={offset})"
                )
                
                # Send emails for this batch
                sent, failed = await self._send_batch_emails(
                    participants=participants,
                    event_type=event_type,
                    event=event,
                    batch_number=batch_number
                )
                
                total_sent += sent
                total_failed += failed
                
                # Move to next batch
                offset += self.batch_size
                batch_number += 1
            
            # Final summary
            logger.info(
                f"Processing complete for event_id={event.event_id}: "
                f"{total_sent} emails sent successfully, "
                f"{total_failed} failed out of {total_participants} total"
            )
    
    async def _send_batch_emails(
        self,
        participants: list,
        event_type: str,
        event,  # Event object
        batch_number: int
    ) -> tuple[int, int]:
        """
        Send emails to a batch of participants.
        
        Args:
            participants: List of Participant objects
            event_type: Type of event
            event: Event object with all details
            batch_number: Current batch number (for logging)
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        logger.info(f"Sending emails for batch {batch_number}...")
        
        # Prepare email data for all participants
        email_tasks = []
        for participant in participants:
            # Render template for this participant
            rendered = EmailTemplateLoader.render_template(
                event_type=event_type,
                event=event,
                name=participant.name
            )
            
            email_tasks.append((
                participant.email,
                rendered['subject'],
                rendered['body']
            ))
        
        # Send all emails in this batch concurrently
        successful, failed = await self.email_service.send_batch(email_tasks)
        
        logger.info(
            f"Batch {batch_number} complete: "
            f"{successful} sent, {failed} failed"
        )
        
        return successful, failed


def process_message_sync(message: NotificationMessage):
    """
    Synchronous wrapper for processing messages.
    This is called by the queue listener.
    
    Args:
        message: NotificationMessage DTO
    """
    processor = NotificationProcessor()
    asyncio.run(processor.process(message))
