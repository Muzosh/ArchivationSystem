import json
from datetime import datetime
from uuid import uuid4

import pika

from ..database.archived_file import ArchivedFile
from ..database.db_library import DatabaseHandler, MysqlConnection
from ..rabbitmq_connection.task_consumer import ConnectionMaker

# from common.exceptions import WrongRecordFormatCustomException - was unused


def format_task_message(file_id: int):
    task_message = {
        "task": "retimestamp",
        "file_id": file_id,
    }
    return json.dumps(task_message)


def make_task(channel, queue, task_message):
    channel.basic_publish(
        exchange="",
        routing_key=queue,
        properties=pika.BasicProperties(correlation_id=str(uuid4())),
        body=task_message,
    )


def publish_retimestamping_tasks(files_to_retimestamp: list, config: dict):
    c_maker = ConnectionMaker(config.get("rabbitmq_connection"))
    connection = c_maker.make_connection()
    channel = connection.channel()

    for file_to_retimestamp in files_to_retimestamp:
        make_task(
            channel,
            config["rabbitmq_info"].get("task_queue"),
            format_task_message(file_to_retimestamp),
        )
    channel.close()
    connection.close()


# This method can be done via 1 sql script
def get_files_to_retimestamp(db_config):
    files_to_retimestamp = {}
    with MysqlConnection(db_config) as db_connection:
        db_handler = DatabaseHandler(db_connection)
        file_ids = db_handler.get_all_file_id()
        for file_id in file_ids:
            archived_file = (
                db_handler.get_specific_archived_file_record_by_file_id(
                    file_id
                )
            )
            if compare_expiration_date(archived_file):
                files_to_retimestamp.add(file_id)
    return list(files_to_retimestamp)


def compare_expiration_date(file_rec: ArchivedFile):
    difference = file_rec.ExpirationDateTS - datetime.now()
    return difference < 2


def run_checker_controller(config):
    print("Checking files to be validated...")
    list_of_files_to_retimestamp = get_files_to_retimestamp(
        config.get("db_config")
    )

    print(
        "Number of files to be retimestamped: ",
        len(list_of_files_to_retimestamp),
    )
    if len(list_of_files_to_retimestamp) == 0:
        print("Done")
        return
    
    print("Publishing tasks...")
    publish_retimestamping_tasks(list_of_files_to_retimestamp, config)
    print("Done")
