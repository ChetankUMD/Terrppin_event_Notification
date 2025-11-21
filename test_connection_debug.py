import pika
import sys

def test_connection():
    print("Testing connection to LavinMQ at localhost:5672...")
    try:
        # Explicitly try to connect
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        if connection.is_open:
            print("SUCCESS: Successfully connected to LavinMQ!")
            connection.close()
            return True
    except Exception as e:
        print(f"FAILURE: Connection failed. Error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
