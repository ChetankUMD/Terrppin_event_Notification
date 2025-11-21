"""
Repository for event reminder operations.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
from data.database import get_notification_session
from data.reminder_model import EventReminder
import logging

logger = logging.getLogger(__name__)


class ReminderRepository:
    """Repository for managing event reminders."""
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize repository with optional session.
        
        Args:
            session: SQLAlchemy session (if None, creates new notification session)
        """
        if session:
            self.session = session
            self._owns_session = False
        else:
            self.session = get_notification_session()
            self._owns_session = True
    
    def get_pending_one_day_reminders(self) -> List[EventReminder]:
        """
        Get reminders where before_one_day <= now and not sent.
        
        Returns:
            List of EventReminder objects
        """
        try:
            now = datetime.now(timezone.utc)
            
            query = text("""
                SELECT id, event_id, before_one_day, before_one_hour,
                       notification_sent_for_one_day, notification_sent_for_one_hour
                FROM event_reminders
                WHERE before_one_day <= :now
                AND notification_sent_for_one_day = false
                ORDER BY before_one_day
            """)
            
            result = self.session.execute(query, {"now": now})
            logger.debug(f"Found {result} pending one-day reminders")
            reminders = []
            for row in result:
                reminder = EventReminder(
                    id=row.id,
                    event_id=row.event_id,
                    before_one_day=row.before_one_day,
                    before_one_hour=row.before_one_hour,
                    notification_sent_for_one_day=row.notification_sent_for_one_day,
                    notification_sent_for_one_hour=row.notification_sent_for_one_hour
                )
                reminders.append(reminder)
            
            logger.debug(f"Found {len(reminders)} pending one-day reminders")
            return reminders
            
        except Exception as e:
            logger.error(f"Error fetching one-day reminders: {e}")
            raise
    
    def get_pending_one_hour_reminders(self) -> List[EventReminder]:
        """
        Get reminders where before_one_hour <= now and not sent.
        
        Returns:
            List of EventReminder objects
        """
        try:
            now = datetime.now(timezone.utc)
            
            query = text("""
                SELECT id, event_id, before_one_day, before_one_hour,
                       notification_sent_for_one_day, notification_sent_for_one_hour
                FROM event_reminders
                WHERE before_one_hour <= :now
                AND notification_sent_for_one_hour = false
                ORDER BY before_one_hour
            """)
            
            result = self.session.execute(query, {"now": now})
            
            reminders = []
            for row in result:
                reminder = EventReminder(
                    id=row.id,
                    event_id=row.event_id,
                    before_one_day=row.before_one_day,
                    before_one_hour=row.before_one_hour,
                    notification_sent_for_one_day=row.notification_sent_for_one_day,
                    notification_sent_for_one_hour=row.notification_sent_for_one_hour
                )
                reminders.append(reminder)
            
            logger.debug(f"Found {len(reminders)} pending one-hour reminders")
            return reminders
            
        except Exception as e:
            logger.error(f"Error fetching one-hour reminders: {e}")
            raise
    
    def mark_one_day_sent(self, reminder_id: int) -> bool:
        """
        Mark one-day reminder as sent.
        
        Args:
            reminder_id: Reminder ID
            
        Returns:
            True if updated successfully
        """
        try:
            query = text("""
                UPDATE event_reminders
                SET notification_sent_for_one_day = true
                WHERE id = :reminder_id
            """)
            
            self.session.execute(query, {"reminder_id": reminder_id})
            self.session.commit()
            
            logger.debug(f"Marked one-day reminder {reminder_id} as sent")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error marking one-day reminder as sent: {e}")
            raise
    
    def mark_one_hour_sent(self, reminder_id: int) -> bool:
        """
        Mark one-hour reminder as sent.
        
        Args:
            reminder_id: Reminder ID
            
        Returns:
            True if updated successfully
        """
        try:
            query = text("""
                UPDATE event_reminders
                SET notification_sent_for_one_hour = true
                WHERE id = :reminder_id
            """)
            
            self.session.execute(query, {"reminder_id": reminder_id})
            self.session.commit()
            
            logger.debug(f"Marked one-hour reminder {reminder_id} as sent")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error marking one-hour reminder as sent: {e}")
            raise
    
    def close(self):
        """Close the session if owned by this repository."""
        if self._owns_session and self.session:
            self.session.close()
            logger.debug("Repository session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
