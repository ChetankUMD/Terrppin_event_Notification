"""
Configuration settings for the notification service.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class LavinMQConfig:
    """LavinMQ connection configuration."""
    host: str = os.getenv('LAVINMQ_HOST', 'localhost')
    port: int = int(os.getenv('LAVINMQ_PORT', '5672'))
    username: str = os.getenv('LAVINMQ_USERNAME', 'guest')
    password: str = os.getenv('LAVINMQ_PASSWORD', 'guest')
    queue_name: str = os.getenv('LAVINMQ_QUEUE', 'event_notifications')
    virtual_host: str = os.getenv('LAVINMQ_VHOST', '/')


@dataclass
class DatabaseConfig:
    """Database configuration."""
    # Main database (for bookings)
    connection_string: str = os.getenv(
        'DATABASE_URL',
        'sqlite:///notification_service.db'
    )
    # Notification database (for event_reminder table)
    notification_db_url: str = os.getenv(
        'NOTIFICATION_DATABASE_URL',
        os.getenv('DATABASE_URL', 'sqlite:///notification_service.db')  # Fallback to main DB
    )
    echo: bool = os.getenv('DATABASE_ECHO', 'False').lower() == 'true'


@dataclass
class EmailConfig:
    """Email service configuration."""
    # Provider selection: 'smtp' or 'sendgrid'
    provider: str = os.getenv('EMAIL_PROVIDER', 'smtp')
    
    # SMTP configuration
    smtp_host: str = os.getenv('SMTP_HOST', 'localhost')
    smtp_port: int = int(os.getenv('SMTP_PORT', '587'))
    smtp_username: str = os.getenv('SMTP_USERNAME', '')
    smtp_password: str = os.getenv('SMTP_PASSWORD', '')
    use_tls: bool = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'
    
    # SendGrid configuration
    sendgrid_api_key: str = os.getenv('SENDGRID_API_KEY', '')
    
    # Common configuration
    from_email: str = os.getenv('FROM_EMAIL', 'notifications@example.com')
    from_name: str = os.getenv('FROM_NAME', 'Notification Service')
    
    # Dummy mode for testing without real email sending
    dummy_mode: bool = os.getenv('EMAIL_DUMMY_MODE', 'True').lower() == 'true'


@dataclass
class ProcessorConfig:
    """Notification processor configuration."""
    batch_size: int = int(os.getenv('BATCH_SIZE', '100'))
    max_retries: int = 3
    retry_delay: int = 5  # seconds


@dataclass
class BookingServiceConfig:
    """Booking service API configuration."""
    base_url: str = os.getenv('BOOKING_SERVICE_URL', 'http://localhost:8000')
    timeout: int = int(os.getenv('BOOKING_SERVICE_TIMEOUT', '30'))


@dataclass
class SchedulerConfig:
    """Scheduler configuration."""
    cron_expression: str = os.getenv('SCHEDULER_INTERVAL', '* * * * *')

@dataclass
class APIConfig:
    """API server configuration."""
    host: str = os.getenv('API_HOST', '0.0.0.0')
    port: int = int(os.getenv('API_PORT', '8001'))
    enabled: bool = os.getenv('API_ENABLED', 'True').lower() == 'true'


@dataclass
class Settings:
    """Application settings container."""
    lavinmq: LavinMQConfig = None
    database: DatabaseConfig = None
    email: EmailConfig = None
    processor: ProcessorConfig = None
    scheduler: SchedulerConfig = None
    booking_service: BookingServiceConfig = None
    api: APIConfig = None
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    def __post_init__(self):
        """Initialize config objects if not provided."""
        if self.lavinmq is None:
            self.lavinmq = LavinMQConfig()
        if self.database is None:
            self.database = DatabaseConfig()
        if self.email is None:
            self.email = EmailConfig()
        if self.processor is None:
            self.processor = ProcessorConfig()
        if self.scheduler is None:
            self.scheduler = SchedulerConfig()
        if self.booking_service is None:
            self.booking_service = BookingServiceConfig()
        if self.api is None:
            self.api = APIConfig()


# Global settings instance
settings = Settings()
