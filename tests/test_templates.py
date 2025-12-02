"""
Unit tests for email templates.
"""
import pytest
from templates.email_templates import EmailTemplateLoader
from models.dto import Event


class TestEmailTemplates:
    """Test suite for EmailTemplateLoader."""
    
    @pytest.fixture
    def sample_event(self):
        """Create a sample event."""
        return Event(
            event_id="event-123",
            event_name="Tech Conference 2024",
            description="A great tech event",
            start_time="2024-12-15T10:00:00",
            end_time="2024-12-15T12:00:00",
            organizer_id="organizer-1",
            location="Convention Center",
            remaining_seats=50
        )
    
    def test_get_template_event_created(self):
        """Test getting event_created template."""
        template = EmailTemplateLoader.get_template('event_created')
        
        assert 'subject' in template
        assert 'body' in template
        assert 'New Event' in template['subject']
    
    def test_get_template_event_updated(self):
        """Test getting event_updated template."""
        template = EmailTemplateLoader.get_template('event_updated')
        
        assert 'subject' in template
        assert 'body' in template
        assert 'Updated' in template['subject']
    
    def test_get_template_event_reminder(self):
        """Test getting event_reminder template."""
        template = EmailTemplateLoader.get_template('event_reminder')
        
        assert 'subject' in template
        assert 'body' in template
        assert 'Reminder' in template['subject']
    
    def test_get_template_invalid_type(self):
        """Test getting template with invalid type raises error."""
        with pytest.raises(ValueError, match="No template found"):
            EmailTemplateLoader.get_template('invalid_type')
    
    def test_render_template_event_created(self, sample_event):
        """Test rendering event_created template."""
        rendered = EmailTemplateLoader.render_template(
            event_type='event_created',
            event=sample_event,
            name="John Doe"
        )
        
        assert 'subject' in rendered
        assert 'body' in rendered
        assert "Tech Conference 2024" in rendered['subject']
        assert "John Doe" in rendered['body']
        assert "Convention Center" in rendered['body']
        assert "<html>" in rendered['body']
    
    def test_render_template_event_updated(self, sample_event):
        """Test rendering event_updated template."""
        rendered = EmailTemplateLoader.render_template(
            event_type='event_updated',
            event=sample_event,
            name="Jane Smith"
        )
        
        assert "Tech Conference 2024" in rendered['subject']
        assert "Jane Smith" in rendered['body']
        assert "updated" in rendered['body'].lower()
    
    def test_render_template_event_reminder(self, sample_event):
        """Test rendering event_reminder template."""
        sample_event.reminder_type = "one_day"
        
        rendered = EmailTemplateLoader.render_template(
            event_type='event_reminder',
            event=sample_event,
            name="Bob Johnson"
        )
        
        assert "Tech Conference 2024" in rendered['subject']
        assert "Bob Johnson" in rendered['body']
        assert "reminder" in rendered['body'].lower()
        assert "1 Day" in rendered['body']
    
    def test_render_template_with_description(self, sample_event):
        """Test that description is included when present."""
        rendered = EmailTemplateLoader.render_template(
            event_type='event_created',
            event=sample_event,
            name="Alice Brown"
        )
        
        assert sample_event.description in rendered['body']
    
    def test_render_template_without_description(self, sample_event):
        """Test rendering when no description is provided."""
        sample_event.description = None
        
        rendered = EmailTemplateLoader.render_template(
            event_type='event_created',
            event=sample_event,
            name="Charlie Davis"
        )
        
        assert 'Charlie Davis' in rendered['body']
        # Should still be valid HTML
        assert '<html>' in rendered['body']
    
    def test_all_templates_have_required_fields(self):
        """Test that all templates have subject and body."""
        for event_type in ['event_created', 'event_updated', 'event_reminder', 'event_cancelled']:
            template = EmailTemplateLoader.get_template(event_type)
            assert 'subject' in template
            assert 'body' in template
            assert len(template['subject']) > 0
            assert len(template['body']) > 0
