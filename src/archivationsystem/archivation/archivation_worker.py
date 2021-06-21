import json
import logging

# from contextlib import closing - was unused
from ..common.exception_wrappers import task_exceptions_wrapper
from ..common.exceptions import WrongTaskCustomException
from ..common.setup_logger import setup_logger
from ..database.db_library import DatabaseHandler, MysqlConnection
from ..rabbitmq_connection.task_consumer import (
    ConnectionMaker,
    TaskConsumer,
)
from .archiver import Archiver

logger = logging.getLogger("archivation_system_logging")


class ArchivationWorker:
    """
    Worker class responsible for creating
    rabbitmq connection and creating task consumer.
    It will set callback function to consumer before
    starting him.
    All exceptions known possible exceptions are catched
    in exception wrappers
    """

    def __init__(self, config):
        self.db_config = config.get("db_config")
        self.rmq_config = config.get("rabbitmq_connection")
        self.connection = ConnectionMaker(self.rmq_config)
        self.task_consumer = TaskConsumer(
            self.connection, config.get("rabbitmq_info")
        )
        self.task_consumer.set_callback(self.archive)
        self.archivation_config = config.get("archivation_system_info")

    def run(self):
        logger.info(
            "[archivation_worker] starting archivation worker consumer"
        )
        self.task_consumer.start()

    @task_exceptions_wrapper
    def archive(self, body):
        """
        Callback function which will be executed on task.
        It needs correct task body otherwise it will throw
        WrongTask Exception
        """
        logger.info(
            "[archivation_worker] recieved task with body: %s", str(body)
        )

        logger.debug("[archivation_worker] creation of database connection")
        with MysqlConnection(self.db_config) as db_connection:
            db_handler = DatabaseHandler(db_connection)
            archiver = Archiver(db_handler, self.archivation_config)
            path, owner = self._parse_message_body(body)
            logger.info(
                "[archivation_worker] executing archivation of file, path: %s"
                " , owner: %s",
                str(path),
                str(owner),
            )
            result = archiver.archive(path, owner)
            logger.info("[archivation_worker] validation was finished")
        return result

    def _parse_message_body(self, body):
        body = json.loads(body)
        if not body.get("task") == "archive":
            logger.warning(
                "incorrect task label for archivation worker, body: %s",
                str(body),
            )
            raise WrongTaskCustomException("task is not for this worker")
        file_path = body.get("file_path")
        owner = body.get("owner_name")
        return file_path, owner


def run_worker(config):
    """
    This function will setup logger and execute worker
    """
    setup_logger(config.get("rabbitmq_logging"))
    arch_worker = ArchivationWorker(config)
    arch_worker.run()
