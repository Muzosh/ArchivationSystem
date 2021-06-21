import logging
import time
import pika
from uuid import uuid4
import json

from archivationsystem.common.setup_logger import setup_logger
from archivationsystem.rabbitmq_connection.task_consumer import (
    ConnectionMaker,
    TaskConsumer,
)

logger = logging.getLogger("archivation_system_logging")


def run():
    connection = ConnectionMaker(
        {
            "host": "192.168.100.112",
            "virtual_host": "archivationsystem",
            "port": "5672",
            "credentials": {
                "name": "ncadmin",
                "password": "ncadmin",
            },
            "enable_ssl": False,
        }
    )
    task_consumer = TaskConsumer(
        connection,
        {
            "consumer_ID": "TestConsumerID",
            "task_queue": "archivation",
            "control_exchange": "control",
        },
    )
    task_consumer.set_callback(job)
    task_consumer.start()


def send_messages():
    c_maker = ConnectionMaker(
        {
            "host": "192.168.100.112",
            "virtual_host": "archivationsystem",
            "port": "5672",
            "credentials": {
                "name": "ncadmin",
                "password": "ncadmin",
            },
            "enable_ssl": False,
        }
    )
    connection = c_maker.make_connection()
    channel = connection.channel()

    for x in range(10):
        task_message = {
            "task": "test",
            "file_path": x,
            "owner_name": "tester",
        }
        time.sleep(1)
        channel.basic_publish(
            exchange="",
            routing_key="archivation",
            properties=pika.BasicProperties(correlation_id=str(uuid4())),
            body=json.dumps(task_message),
        )
        print("Message published: ", task_message)
    channel.close()


def job(body):

    print(body)
    return "OK"


def main():
    setup_logger(
        {
            "host": "192.168.100.112",
            "port": "5672",
            "username": "ncadmin",
            "password": "ncadmin",
            "logging_level": "DEBUG",
        }
    )
    send_messages()
    run()


if __name__ == "__main__":
    main()
