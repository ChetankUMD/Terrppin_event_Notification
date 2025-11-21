"""
Repository for participant data access with pagination support.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from data.database import Participant, get_session, close_session
import logging

logger = logging.getLogger(__name__)


class ParticipantRepository:
    """Repository for managing participant data access."""
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize repository.
        
        Args:
            session: Optional SQLAlchemy session. If not provided, a new session will be created.
        """
        self.session = session
        self._owns_session = session is None
        if self._owns_session:
            self.session = get_session()
    
    def get_participants_by_event(
        self, 
        event_id: str,  # Changed to str for UUID support
        offset: int = 0, 
        limit: int = 100
    ) -> List[Participant]:
        """
        Retrieve participants for a specific event with pagination.
        Queries from the bookings table directly.
        
        Args:
            event_id: The event ID to filter participants (UUID string)
            offset: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of Participant objects
        """
        try:
            logger.debug(
                f"Fetching participants for event_id={event_id}, "
                f"offset={offset}, limit={limit}"
            )
            
            # Query from bookings table
            from sqlalchemy import text
            query = text("""
                SELECT booking_id, event_id, user_id, user_email, 
                       event_name, booking_time, status
                FROM bookings
                WHERE event_id = :event_id
                AND status = 'confirmed'
                ORDER BY booking_time
                OFFSET :offset
                LIMIT :limit
            """)
            
            result = self.session.execute(
                query,
                {"event_id": event_id, "offset": offset, "limit": limit}
            )
            
            # Convert to Participant objects
            participants = []
            for row in result:
                participant = Participant(
                    booking_id=row.booking_id,
                    event_id=row.event_id,
                    user_id=row.user_id,
                    user_email=row.user_email,
                    event_name=row.event_name,
                    booking_time=str(row.booking_time) if row.booking_time else None,
                    status=row.status
                )
                participants.append(participant)
            
            logger.debug(f"Retrieved {len(participants)} participants from bookings table")
            return participants
            
        except Exception as e:
            logger.error(f"Error fetching participants from bookings: {e}")
            raise
    
    def count_participants_by_event(self, event_id: str) -> int:
        """
        Count total participants for an event from bookings table.
        
        Args:
            event_id: The event ID to count participants for (UUID string)
            
        Returns:
            Total number of confirmed bookings
        """
        try:
            from sqlalchemy import text
            query = text("""
                SELECT COUNT(*) 
                FROM bookings 
                WHERE event_id = :event_id 
                AND status = 'confirmed'
            """)
            
            result = self.session.execute(query, {"event_id": event_id})
            count = result.scalar()
            
            logger.debug(f"Total participants for event_id={event_id}: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Error counting participants: {e}")
            raise
    
    def add_participant(
        self, 
        booking_id: str,
        event_id: str,
        user_id: str,
        user_email: str,
        event_name: str = None,
        booking_time: str = None,
        status: str = 'confirmed'
    ) -> Participant:
        """
        Add a new participant/booking to the database.
        
        Args:
            booking_id: Unique booking ID (UUID)
            event_id: Event ID (UUID)
            user_id: User ID (UUID)
            user_email: User email address
            event_name: Name of the event (optional)
            booking_time: Booking timestamp (optional)
            status: Booking status (default: 'confirmed')
            
        Returns:
            Created Participant object
        """
        try:
            participant = Participant(
                booking_id=booking_id,
                event_id=event_id,
                user_id=user_id,
                user_email=user_email,
                event_name=event_name,
                booking_time=booking_time,
                status=status
            )
            self.session.add(participant)
            self.session.commit()
            self.session.refresh(participant)
            
            logger.info(f"Added participant: {participant}")
            return participant
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding participant: {e}")
            raise
    
    def add_participants_from_bookings(self, bookings: list) -> int:
        """
        Bulk add participants from booking data.
        
        Args:
            bookings: List of booking dictionaries
            
        Returns:
            Number of participants added
        """
        count = 0
        for booking in bookings:
            try:
                self.add_participant(
                    booking_id=booking['booking_id'],
                    event_id=booking['event_id'],
                    user_id=booking['user_id'],
                    user_email=booking['user_email'],
                    event_name=booking.get('event_name'),
                    booking_time=booking.get('booking_time'),
                    status=booking.get('status', 'confirmed')
                )
                count += 1
            except Exception as e:
                logger.error(f"Failed to add booking {booking.get('booking_id')}: {e}")
                continue
        
        logger.info(f"Added {count} participants from bookings")
        return count
    
    def close(self):
        """Close the session if it's owned by this repository."""
        if self._owns_session and self.session:
            close_session(self.session)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
