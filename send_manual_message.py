import pika
import json
from config.settings import settings

def send_test_message():
    print("Connecting to LavinMQ...")
    if hasattr(settings.lavinmq, 'connection_url') and settings.lavinmq.connection_url:
        print("Connecting via URL...")
        params = pika.URLParameters(settings.lavinmq.connection_url)
    else:
        print("Connecting via host/port...")
        params = pika.ConnectionParameters(
            host=settings.lavinmq.host,
            port=settings.lavinmq.port,
            credentials=pika.PlainCredentials(settings.lavinmq.username, settings.lavinmq.password)
        )

    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    
    queue_name = settings.lavinmq.queue_name
    channel.queue_declare(queue=queue_name, durable=True)
    
    message = {
        "type": "event_reminder",
        "event_id": "123",
        "reminder_type": "one_day"
    }
    
    print(f"Sending message to {queue_name}: {message}")
    
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        )
    )
    
    print("Message sent!")
    connection.close()

if __name__ == "__main__":
    send_test_message()
