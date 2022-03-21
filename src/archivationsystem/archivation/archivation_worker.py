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

logger = logging.getLogger("archiving_system_logging")


class ArchivingWorker:
    """
    Worker class responsible for creating
    rabbitmq connection and creating task consumer.
    It will set callback function to consumer before
    starting him.
    All exceptions known possible exceptions are catched
    in exception wrappers
    """

    def __init__(self, config: dict):
        self.db_config = config.get("db_config")
        self.rabbitmq_connection = config.get("rabbitmq_connection")
        self.connection = ConnectionMaker(self.rabbitmq_connection)
        self.task_consumer = TaskConsumer(
            self.connection, config.get("rabbitmq_info")
        )
        self.task_consumer.set_callback(self.archive)
        self.archiving_config = config.get("archiving_system_info")

    def run(self):
        logger.info("starting archiving task consumer")
        self.task_consumer.start()

    @task_exceptions_wrapper
    def archive(self, jbody):
        """
        Callback function which will be executed on task.
        It needs correct task body otherwise it will throw
        WrongTask Exception
        """
        logger.debug("recieved task with body: %s", str(jbody))

        logger.info("creating database connection")
        with MysqlConnection(self.db_config) as db_connection:
            db_handler = DatabaseHandler(db_connection)
            archiver = Archiver(db_handler, self.archiving_config)
            file_path, owner = self._parse_message_body(jbody)

            logger.debug(
                "executing archiving of file id and owner: %s and %s",
                str(file_path),
                str(owner),
            )
            result = archiver.archive(file_path, owner)
        return result

    def _parse_message_body(self, jbody):
        body = json.loads(jbody)
        if not body.get("task") == "archive":
            logger.error(
                "incorrect task for archiving worker: task=%s",
                str(body.get("task")),
            )
            raise WrongTaskCustomException(
                "incorrect task for archiving worker: task={}".format(
                    str(body.get("task"))
                ),
            )
        return body.get("file_path"), body.get("owner_name")


def run_worker(config):
    """
    This function will setup logger and execute worker
    """
    setup_logger(config.get("rabbitmq_logging"))
    arch_worker = ArchivingWorker(config)
    arch_worker.run()
