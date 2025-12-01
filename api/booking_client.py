"""
API client for the Booking service.
"""
import httpx
from typing import List, Optional
from config.settings import settings
from models.dto import BookingBatchResponse
import logging

logger = logging.getLogger(__name__)


class BookingAPIClient:
    """Client for interacting with the Booking service API."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        """
        Initialize the Booking API client.
        
        Args:
            base_url: Base URL for the booking service (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
        """
        self.base_url = base_url or settings.booking_service.base_url
        self.timeout = timeout or settings.booking_service.timeout
        
        # Remove trailing slash from base_url if present
        self.base_url = self.base_url.rstrip('/')
        
        logger.info(
            f"BookingAPIClient initialized with base_url={self.base_url}, "
            f"timeout={self.timeout}s"
        )
    
    def get_bookings_count(self, event_id: str) -> int:
        """
        Get the count of bookings for a specific event.
        
        Args:
            event_id: The event ID to count bookings for
            
        Returns:
            Number of confirmed bookings
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        url = f"{self.base_url}/bookings/count"
        params = {"event_id": event_id}
        
        try:
            logger.debug(f"Fetching booking count for event_id={event_id}")
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                
                # The API returns: {"event_id": "...", "total_bookings": X}
                data = response.json()
                count = data.get('total_bookings', 0) if isinstance(data, dict) else 0
                
                logger.info(f"Retrieved booking count for event_id={event_id}: {count}")
                return count
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching booking count: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching booking count: {e}")
            raise
    
    def get_bookings_batch(
        self,
        event_id: str,
        offset: int = 0,
        batch_size: int = 5
    ) -> List[BookingBatchResponse]:
        """
        Get a batch of bookings for a specific event.
        
        Args:
            event_id: The event ID to fetch bookings for
            offset: Number of records to skip (for pagination)
            batch_size: Maximum number of records to return
            
        Returns:
            List of BookingBatchResponse objects
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        url = f"{self.base_url}/bookings/batch"
        params = {
            "event_id": event_id,
            "offset": offset,
            "batch_size": batch_size
        }
        
        try:
            logger.debug(
                f"Fetching booking batch for event_id={event_id}, "
                f"offset={offset}, batch_size={batch_size}"
            )
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)
                
                # Handle 404 as "no more results" rather than an error
                if response.status_code == 404:
                    logger.info(
                        f"No more bookings available for event_id={event_id} "
                        f"at offset={offset} (404 response)"
                    )
                    return []
                
                response.raise_for_status()
                
                data = response.json()
                
                # Handle empty response
                if not data:
                    logger.info(f"Empty batch returned for event_id={event_id}, offset={offset}")
                    return []
                
                # Convert API response to BookingBatchResponse objects
                bookings = [
                    BookingBatchResponse.from_dict(booking)
                    for booking in data
                ]
                
                logger.info(
                    f"Retrieved {len(bookings)} bookings for event_id={event_id}, "
                    f"offset={offset}"
                )
                return bookings
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching booking batch: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching booking batch: {e}")
            raise
