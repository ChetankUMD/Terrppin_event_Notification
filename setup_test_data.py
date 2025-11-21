import uuid
from datetime import datetime, timedelta, timezone
from data.database import init_database, get_session, get_notification_session
from data.repository import ParticipantRepository
from data.reminder_model import EventReminder
from sqlalchemy.orm import Session

def setup_test_data():
    print("Initializing database...")
    init_database()
    
    event_id = "123"
    
    # 1. Add Participant
    print("Adding test participant...")
    with ParticipantRepository() as repo:
        # Check if participant already exists to avoid duplicates
        participants = repo.get_participants_by_event(event_id)
        if not participants:
            repo.add_participant(
                booking_id=str(uuid.uuid4()),
                event_id=event_id,
                user_id=str(uuid.uuid4()),
                user_email="test_participant@example.com",
                event_name="Test Event",
                booking_time=datetime.now().isoformat(),
                status="confirmed"
            )
            print("Participant added.")
        else:
            print("Participant already exists.")

    # 2. Add Event Reminder
    print("Adding test event reminder...")
    session = get_notification_session()
    try:
        # Check if reminder exists
        existing = session.query(EventReminder).filter_by(event_id=event_id).first()
        
        if not existing:
            reminder = EventReminder(
                event_id=event_id,
                before_one_day=datetime.now(timezone.utc) - timedelta(minutes=1), # In the past
                before_one_hour=datetime.now(timezone.utc) + timedelta(hours=1),
                notification_sent_for_one_day=False,
                notification_sent_for_one_hour=False
            )
            session.add(reminder)
            session.commit()
            print("Event reminder added (scheduled for 1 minute ago).")
        else:
            # Reset if exists
            existing.before_one_day = datetime.now(timezone.utc) - timedelta(minutes=1)
            existing.notification_sent_for_one_day = False
            session.commit()
            print("Existing event reminder reset to pending.")
            
    except Exception as e:
        print(f"Error adding reminder: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    setup_test_data()
