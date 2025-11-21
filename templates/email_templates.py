"""
Email template management for different event types.
"""
from typing import Dict
from models.dto import EventType, Event
import logging

logger = logging.getLogger(__name__)


class EmailTemplateLoader:
    """Loads and manages email templates for different event types."""
    
    # HTML email templates
    TEMPLATES: Dict[EventType, Dict[str, str]] = {
        'event_updated': {
            'subject': 'Event Updated: {event_name}',
            'body': """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 30px; margin-top: 0; border-radius: 0 0 5px 5px; }}
        .event-details {{ background-color: white; padding: 20px; margin: 20px 0; border-left: 4px solid #4CAF50; }}
        .detail-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #555; }}
        .value {{ color: #333; }}
        .footer {{ text-align: center; margin-top: 20px; color: #777; font-size: 12px; }}
        .seats {{ color: #4CAF50; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📅 Event Updated</h1>
        </div>
        <div class="content">
            <p>Hello {name},</p>
            <p>The event you are registered for has been updated. Please review the latest details below:</p>
            
            <div class="event-details">
                <h2 style="margin-top: 0; color: #4CAF50;">{event_name}</h2>
                
                <div class="detail-row">
                    <span class="label">📍 Location:</span>
                    <span class="value">{location}</span>
                </div>
                
                <div class="detail-row">
                    <span class="label">🕐 Start Time:</span>
                    <span class="value">{start_time}</span>
                </div>
                
                <div class="detail-row">
                    <span class="label">🕐 End Time:</span>
                    <span class="value">{end_time}</span>
                </div>
                
                <div class="detail-row">
                    <span class="label">💺 Available Seats:</span>
                    <span class="seats">{remaining_seats} seats remaining</span>
                </div>
                
                {description_section}
            </div>
            
            <p>Please make note of any changes to the event schedule or location.</p>
        </div>
        <div class="footer">
            <p>Event ID: {event_id}</p>
            <p>This is an automated notification. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
            """
        },
        'event_created': {
            'subject': 'New Event: {event_name}',
            'body': """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 30px; margin-top: 0; border-radius: 0 0 5px 5px; }}
        .event-details {{ background-color: white; padding: 20px; margin: 20px 0; border-left: 4px solid #2196F3; }}
        .detail-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #555; }}
        .value {{ color: #333; }}
        .footer {{ text-align: center; margin-top: 20px; color: #777; font-size: 12px; }}
        .seats {{ color: #2196F3; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 New Event Created</h1>
        </div>
        <div class="content">
            <p>Hello {name},</p>
            <p>You have been added as a participant to a new event. We're excited to have you join us!</p>
            
            <div class="event-details">
                <h2 style="margin-top: 0; color: #2196F3;">{event_name}</h2>
                
                <div class="detail-row">
                    <span class="label">📍 Location:</span>
                    <span class="value">{location}</span>
                </div>
                
                <div class="detail-row">
                    <span class="label">🕐 Start Time:</span>
                    <span class="value">{start_time}</span>
                </div>
                
                <div class="detail-row">
                    <span class="label">🕐 End Time:</span>
                    <span class="value">{end_time}</span>
                </div>
                
                <div class="detail-row">
                    <span class="label">💺 Available Seats:</span>
                    <span class="seats">{remaining_seats} seats remaining</span>
                </div>
                
                {description_section}
            </div>
            
            <p>We look forward to seeing you at the event!</p>
        </div>
        <div class="footer">
            <p>Event ID: {event_id}</p>
            <p>This is an automated notification. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
            """
        },
        'event_cancelled': {
            'subject': 'Event Cancelled: {event_name}',
            'body': """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 30px; margin-top: 0; border-radius: 0 0 5px 5px; }}
        .event-details {{ background-color: white; padding: 20px; margin: 20px 0; border-left: 4px solid #f44336; }}
        .detail-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #555; }}
        .value {{ color: #333; text-decoration: line-through; }}
        .footer {{ text-align: center; margin-top: 20px; color: #777; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>❌ Event Cancelled</h1>
        </div>
        <div class="content">
            <p>Hello {name},</p>
            <p>We regret to inform you that the following event has been cancelled:</p>
            
            <div class="event-details">
                <h2 style="margin-top: 0; color: #f44336;">{event_name}</h2>
                
                <div class="detail-row">
                    <span class="label">📍 Location:</span>
                    <span class="value">{location}</span>
                </div>
                
                <div class="detail-row">
                    <span class="label">🕐 Was Scheduled:</span>
                    <span class="value">{start_time} - {end_time}</span>
                </div>
                
                {description_section}
            </div>
            
            <p>We apologize for any inconvenience this may cause.</p>
        </div>
        <div class="footer">
            <p>Event ID: {event_id}</p>
            <p>This is an automated notification. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
            """
        },
        'event_reminder': {
            'subject': 'Reminder: {event_name} - {reminder_message}',
            'body': """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #FF9800; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 30px; margin-top: 0; border-radius: 0 0 5px 5px; }}
        .event-details {{ background-color: white; padding: 20px; margin: 20px 0; border-left: 4px solid #FF9800; }}
        .detail-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #555; }}
        .value {{ color: #333; }}
        .footer {{ text-align: center; margin-top: 20px; color: #777; font-size: 12px; }}
        .reminder-badge {{ background-color: #FF9800; color: white; padding: 5px 15px; border-radius: 20px; display: inline-block; margin: 10px 0; }}
        .seats {{ color: #FF9800; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⏰ Event Reminder</h1>
        </div>
        <div class="content">
            <p>Hello {name},</p>
            <p><span class="reminder-badge">{reminder_message}</span></p>
            <p>This is a friendly reminder about your upcoming event:</p>
            
            <div class="event-details">
                <h2 style="margin-top: 0; color: #FF9800;">{event_name}</h2>
                
                <div class="detail-row">
                    <span class="label">📍 Location:</span>
                    <span class="value">{location}</span>
                </div>
                
                <div class="detail-row">
                    <span class="label">🕐 Start Time:</span>
                    <span class="value">{start_time}</span>
                </div>
                
                <div class="detail-row">
                    <span class="label">🕐 End Time:</span>
                    <span class="value">{end_time}</span>
                </div>
                
                <div class="detail-row">
                    <span class="label">💺 Available Seats:</span>
                    <span class="seats">{remaining_seats} seats remaining</span>
                </div>
                
                {description_section}
            </div>
            
            <p>We look forward to seeing you at the event!</p>
        </div>
        <div class="footer">
            <p>Event ID: {event_id}</p>
            <p>This is an automated notification. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
            """
        }
    }
    
    @classmethod
    def get_template(cls, event_type: EventType) -> Dict[str, str]:
        """
        Get email template for a specific event type.
        
        Args:
            event_type: Type of event (event_updated, event_created, event_cancelled)
            
        Returns:
            Dictionary with 'subject' and 'body' keys
            
        Raises:
            ValueError: If event type is not supported
        """
        if event_type not in cls.TEMPLATES:
            raise ValueError(f"No template found for event type: {event_type}")
        
        logger.debug(f"Loading template for event type: {event_type}")
        return cls.TEMPLATES[event_type]
    
    @classmethod
    def render_template(
        cls, 
        event_type: EventType, 
        event: Event,
        name: str
    ) -> Dict[str, str]:
        """
        Render email template with event and participant data.
        
        Args:
            event_type: Type of event
            event: Event object with details
            name: Participant name
            
        Returns:
            Dictionary with rendered 'subject' and 'body'
        """
        template = cls.get_template(event_type)
        
        # Format description section
        description_section = ""
        if event.description:
            description_section = f"""
                <div class="detail-row">
                    <span class="label">📝 Description:</span>
                    <div class="value" style="margin-top: 5px;">{event.description}</div>
                </div>
            """
        
        # Determine reminder message for event_reminder type
        reminder_message = ""
        if event_type == 'event_reminder' and event.reminder_type:
            if event.reminder_type == 'one_day':
                reminder_message = "Starting in 1 Day"
            elif event.reminder_type == 'one_hour':
                reminder_message = "Starting in 1 Hour"
            else:
                reminder_message = "Upcoming Event"
        
        rendered = {
            'subject': template['subject'].format(
                event_name=event.event_name,
                event_id=event.event_id,
                reminder_message=reminder_message
            ),
            'body': template['body'].format(
                name=name,
                event_id=event.event_id,
                event_name=event.event_name,
                location=event.location,
                start_time=event.get_formatted_start_time(),
                end_time=event.get_formatted_end_time(),
                remaining_seats=event.remaining_seats,
                description_section=description_section,
                reminder_message=reminder_message
            )
        }
        
        logger.debug(f"Rendered template for {name}, event={event.event_name}")
        return rendered
