# Script just for consuming and printing logs from run
import pika
from pika.credentials import PlainCredentials


def listen_logs():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host="localhost",
            credentials=PlainCredentials(username="guest", password="guest"),
        )
    )
    channel = connection.channel()

    def callback_print_message(ch, method, properties, body):
        print(body)

    channel.basic_consume("logs", callback_print_message, auto_ack=True)
    channel.start_consuming()


if __name__ == "__main__":
    listen_logs()
