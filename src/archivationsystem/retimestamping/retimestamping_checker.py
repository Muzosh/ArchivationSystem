import json
from datetime import datetime
from uuid import uuid4

import pika

from ..database.archivation_file import ArchivedFile
from ..database.db_library import DatabaseLibrary, MysqlConnection
from ..rabbitmq_connection.task_consumer import ConnectionMaker

# from common.exceptions import WrongRecordFormatCustomException - was unused


def format_task_message(file_id: int):
    task_message = {
        "task": "Retimestamp",
        "file_id": file_id,
    }
    return json.dumps(task_message)


def make_task(channel, queue, task_message):
    channel.basic_publish(
        exchange="",
        routing_key=queue,
        properties=pika.BasicProperties(correlation_id=str(uuid4)),
        body=task_message,
    )


def publish_retimestamping_tasks(
    files_to_retimestamp: list, config_rabbit: dict
):
    c_maker = ConnectionMaker(config_rabbit.get("rabbitmq_connection"))
    connection = c_maker.make_connection()
    channel = connection.channel()

    for file_to_ret in files_to_retimestamp:
        make_task(
            channel,
            config_rabbit["rabbitmq_info"].get("task_queue"),
            format_task_message(file_to_ret),
        )
    channel.close()
    connection.close()


def get_files_to_retimestamp(db_config):
    files_to_retimestamp = set()
    with MysqlConnection(db_config) as db_connection:
        db_api = DatabaseLibrary(db_connection)
        file_ids = db_api.get_all_file_id()
        for f_id in file_ids:
            file_rec = get_file_rec(f_id, db_api)
            if compare_expiration_date(file_rec):
                files_to_retimestamp.add(f_id)
    return list(files_to_retimestamp)


def get_file_rec(file_id, db_api: DatabaseLibrary):
    return db_api.get_specific_archived_file_record_by_file_id(file_id)


def compare_expiration_date(file_rec: ArchivedFile):
    if not isinstance(file_rec.ExpirationDateTS, datetime):
        return False  # LOG IT
    difference = file_rec.ExpirationDateTS - datetime.now()
    if difference.days < 2:
        return True
    return False


def checker_controller(config):
    print("Checking files to be validated")
    list_of_files_to_retimestamp = get_files_to_retimestamp(
        config.get("db_config")
    )
    print(
        "Number of files to be retimestamped: ",
        len(list_of_files_to_retimestamp),
    )
    if len(list_of_files_to_retimestamp) == 0:
        return
    print("Publishing tasks")
    publish_retimestamping_tasks(list_of_files_to_retimestamp, config)
