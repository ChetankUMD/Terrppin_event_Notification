"""
Database setup and models using SQLAlchemy.
"""
from sqlalchemy import create_engine, Integer, String, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


# Create base class for declarative models
class Base(DeclarativeBase):
    pass


class Participant(Base):
    """Participant model representing event bookings/participants."""
    __tablename__ = 'participants'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(String(255), unique=True, nullable=False)
    event_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False)
    user_email = Column(String(255), nullable=False)
    event_name = Column(String(500), nullable=True)
    booking_time = Column(String(100), nullable=True)
    status = Column(String(50), nullable=True, default='confirmed')
    
    # Compatibility property for existing code
    @property
    def email(self):
        """Alias for user_email for backward compatibility."""
        return self.user_email
    
    @property
    def name(self):
        """Extract name from email for backward compatibility."""
        # Extract username from email as name
        return self.user_email.split('@')[0] if self.user_email else 'User'
    
    def __repr__(self):
        return f"<Participant(booking_id={self.booking_id}, event_id={self.event_id}, user_email={self.user_email})>"


# Create database engine
engine = create_engine(
    settings.database.connection_string,
    echo=settings.database.echo
)

# Create notification database engine (for event_reminder table)
notification_engine = create_engine(
    settings.database.notification_db_url,
    echo=settings.database.echo
)

# Session factory
SessionLocal = sessionmaker(bind=engine)

# Notification session factory
NotificationSessionLocal = sessionmaker(bind=notification_engine)


def init_database():
    """Initialize database tables."""
    logger.info("Initializing database...")
    
    # Create tables in main database
    Base.metadata.create_all(bind=engine)
    
    # Create tables in notification database
    Base.metadata.create_all(bind=notification_engine)
    
    logger.info("Database initialized successfully")


def get_session() -> Session:
    """
    Get a new database session for main database (bookings).
    
    Returns:
        SQLAlchemy Session instance
    """
    return SessionLocal()


def get_notification_session() -> Session:
    """
    Get a new database session for notification database (event_reminder).
    
    Returns:
        SQLAlchemy Session instance
    """
    return NotificationSessionLocal()


def close_session(session: Session):
    """
    Close a database session.
    
    Args:
        session: SQLAlchemy Session to close
    """
    if session:
        session.close()
