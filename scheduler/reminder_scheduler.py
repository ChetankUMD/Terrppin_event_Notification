"""
Scheduler for checking and sending event reminders.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from data.reminder_repository import ReminderRepository
from scheduler.queue_publisher import QueuePublisher
import logging

logger = logging.getLogger(__name__)


def check_reminders():
    """
    Check for pending reminders and publish messages to queue.
    This function runs every minute via APScheduler.
    """
    logger.info("Checking for pending event reminders...")
    
    one_day_count = 0
    one_hour_count = 0
    
    try:
        with ReminderRepository() as repo:
            # Check one-day reminders
            one_day_reminders = repo.get_pending_one_day_reminders()
            
            if one_day_reminders:
                logger.info(f"Found {len(one_day_reminders)} pending one-day reminders")
                
                with QueuePublisher() as publisher:
                    for reminder in one_day_reminders:
                        try:
                            # Publish message
                            success = publisher.publish_reminder(
                                event_id=reminder.event_id,
                                reminder_type='one_day'
                            )
                            
                            if success:
                                # Mark as sent
                                repo.mark_one_day_sent(reminder.id)
                                one_day_count += 1
                                logger.info(
                                    f"Sent one-day reminder for event {reminder.event_id}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Failed to process one-day reminder {reminder.id}: {e}"
                            )
                            continue
            
            # Check one-hour reminders
            one_hour_reminders = repo.get_pending_one_hour_reminders()
            
            if one_hour_reminders:
                logger.info(f"Found {len(one_hour_reminders)} pending one-hour reminders")
                
                with QueuePublisher() as publisher:
                    for reminder in one_hour_reminders:
                        try:
                            # Publish message
                            success = publisher.publish_reminder(
                                event_id=reminder.event_id,
                                reminder_type='one_hour'
                            )
                            
                            if success:
                                # Mark as sent
                                repo.mark_one_hour_sent(reminder.id)
                                one_hour_count += 1
                                logger.info(
                                    f"Sent one-hour reminder for event {reminder.event_id}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Failed to process one-hour reminder {reminder.id}: {e}"
                            )
                            continue
        
        if one_day_count > 0 or one_hour_count > 0:
            logger.info(
                f"Reminder check complete: {one_day_count} one-day, "
                f"{one_hour_count} one-hour reminders sent"
            )
        else:
            logger.debug("No pending reminders found")
            
    except Exception as e:
        logger.error(f"Error in reminder check job: {e}")


def start_reminder_scheduler():
    """
    Start the background scheduler for reminder checks.
    
    Returns:
        BackgroundScheduler instance
    """
    from config.settings import settings
    
    logger.info("Starting reminder scheduler...")
    
    scheduler = BackgroundScheduler()
    
    cron_expression = settings.scheduler.cron_expression
    
    # Parse cron expression (minute hour day month day_of_week)
    cron_parts = cron_expression.split()
    if len(cron_parts) != 5:
        logger.error(f"Invalid cron expression: {cron_expression}. Using default: every minute")
        cron_parts = ['*', '*', '*', '*', '*']
    
    # Add job with cron trigger
    scheduler.add_job(
        check_reminders,
        'cron',
        minute=cron_parts[0],
        hour=cron_parts[1],
        day=cron_parts[2],
        month=cron_parts[3],
        day_of_week=cron_parts[4],
        id='check_reminders',
        name='Check Event Reminders',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Reminder scheduler started with cron: {cron_expression}")
    
    return scheduler


def stop_reminder_scheduler(scheduler: BackgroundScheduler):
    """
    Stop the reminder scheduler gracefully.
    
    Args:
        scheduler: BackgroundScheduler instance
    """
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Reminder scheduler stopped")
