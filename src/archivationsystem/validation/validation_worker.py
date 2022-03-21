import json
import logging

from ..common.exception_wrappers import task_exceptions_wrapper
from ..common.exceptions import WrongTaskCustomException
from ..common.setup_logger import setup_logger
from ..database.db_library import DatabaseHandler, MysqlConnection
from ..rabbitmq_connection.task_consumer import ConnectionMaker, TaskConsumer
from .validator import Validator

# from contextlib import closing - was unused


logger = logging.getLogger("archiving_system_logging")


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
        logger.info("starting validation task consumer")
        self.task_consumer.start()

    @task_exceptions_wrapper
    def validate(self, jbody):
        """
        Callback function which will be executed on task.
        It needs correct task body otherwise it will throw
        WrongTask Exception
        """
        logger.debug("recieved task with body: %s", str(jbody))

        logger.debug("creating database connection")
        with MysqlConnection(self.db_config) as db_connection:
            db_handler = DatabaseHandler(db_connection)
            validator = Validator(db_handler, self.validation_config)
            files_info, recipients = self._parse_message_body(jbody)

            logger.debug(
                "executing validation of these files: %s \nfor recipients: %s",
                str(files_info),
                str(recipients),
            )
            result = validator.validate(files_info, recipients)
        return result

    def _parse_message_body(self, body):
        body = json.loads(body)
        if not body.get("task") == "validate":
            logger.warning(
                "incorrect task for validation worker, task: %s",
                str(body.get("task")),
            )
            raise WrongTaskCustomException(
                "incorrect task for validation worker, task: {}".format(
                    str(body.get("task"))
                ),
            )
        return body.get("files_info"), body.get("recipients")


def run_worker(config):
    """
    This function will setup logger and execute worker
    """
    setup_logger(config.get("rabbitmq_logging"))
    arch_worker = ValidationWorker(config)
    arch_worker.run()
