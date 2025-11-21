"""
SQLAlchemy model for event reminders.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from data.database import Base
import logging

logger = logging.getLogger(__name__)


class EventReminder(Base):
    """Event reminder model for scheduled notifications."""
    __tablename__ = 'event_reminders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(255), nullable=False, index=True)
    before_one_day = Column(DateTime, nullable=False, index=True)
    before_one_hour = Column(DateTime, nullable=False, index=True)
    notification_sent_for_one_day = Column(Boolean, default=False, nullable=False)
    notification_sent_for_one_hour = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return (
            f"<EventReminder(id={self.id}, event_id={self.event_id}, "
            f"one_day_sent={self.notification_sent_for_one_day}, "
            f"one_hour_sent={self.notification_sent_for_one_hour})>"
        )
