import json
import logging

from ..common.exception_wrappers import task_exceptions_wrapper
from ..common.exceptions import WrongTaskCustomException
from ..common.setup_logger import setup_logger
from ..database.db_library import DatabaseHandler, MysqlConnection
from ..rabbitmq_connection.task_consumer import ConnectionMaker, TaskConsumer
from .validator import Validator

# from contextlib import closing - was unused


logger = logging.getLogger("Archivation System")


class ValidationWorker:
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
        self.task_consumer.set_callback(self.validate)
        self.validation_config = config.get("validation_info")

    def run(self):
        logger.info("[validation_worker] starting validation worker consumer")
        self.task_consumer.start()

    @task_exceptions_wrapper
    def validate(self, body):
        """
        Callback function which will be executed on task.
        It needs correct task body otherwise it will throw
        WrongTask Exception
        """
        logger.info(
            "[validation_worker] recieved task with body: %s", str(body)
        )

        logger.debug("[validation_worker] creation of database connection")
        with MysqlConnection(self.db_config) as db_connection:
            db_handler = DatabaseHandler(db_connection)
            validator = Validator(db_handler, self.validation_config)
            files_info, recipients = self._parse_message_body(body)
            logger.info(
                "[validation_worker] executing validation of file: %s",
                str(files_info),
            )
            result = validator.validate(files_info, recipients)
            logger.info("[validation_worker] validation was finished")
        return result

    def _parse_message_body(self, body):
        body = json.loads(body)
        if not body["task"] == "Validation":
            logger.warning(
                "incorrect task label for validation worker, body: %s",
                str(body),
            )
            raise WrongTaskCustomException("task is not for this worker")
        files_info = body["files_info"]
        recipients = body["result_recipients"]
        return files_info, recipients


def run_worker(config):
    """
    This function will setup logger and execute worker
    """
    setup_logger(config.get("rabbitmq_logging"))
    arch_worker = ValidationWorker(config)
    arch_worker.run()
