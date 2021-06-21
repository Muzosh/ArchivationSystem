import json
import logging

from ..common.exception_wrappers import task_exceptions_wrapper
from ..common.exceptions import WrongTaskCustomException
from ..common.setup_logger import setup_logger
from ..database.db_library import DatabaseHandler, MysqlConnection
from ..rabbitmq_connection.task_consumer import ConnectionMaker, TaskConsumer
from .retimestamper import Retimestamper

# from contextlib import closing - was unused


logger = logging.getLogger("archivation_system_logging")


class RetimestampingWorker:
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
        self.task_consumer.set_callback(self.retimestamp)
        self.retimestamping_config = config.get("retimestamping_info")

    def run(self):
        logger.info(
            "[retimestamping_worker] starting retimestamping worker consumer"
        )
        self.task_consumer.start()

    @task_exceptions_wrapper
    def retimestamp(self, body):
        """
        Callback function which will be executed on task.
        It needs correct task body otherwise it will throw
        WrongTask Exception
        """
        logger.info(
            "[retimestamping_worker] recieved task with body: %s", str(body)
        )

        logger.debug("[retimestamping_worker] creation of database connection")
        with MysqlConnection(self.db_config) as db_connection:
            db_handler = DatabaseHandler(db_connection)
            retimestamper = Retimestamper(
                db_handler, self.retimestamping_config
            )
            file_id = self._parse_message_body(body)
            logger.info(
                "[retimestamping_worker] executing retimestamping of file"
                " id: %s",
                str(file_id),
            )
            result = retimestamper.retimestamp(file_id)
            logger.info("[retimestamping_worker] retimestamping was finished")
        return result

    def _parse_message_body(self, body):
        body = json.loads(body)
        if not body["task"] == "Retimestamp":
            logger.warning(
                "incorrect task label for retimestamping worker, body: %s",
                str(body),
            )
            raise WrongTaskCustomException("task is not for this worker")
        file_id = body["file_id"]
        return file_id


def run_worker(config):
    """
    This function will setup logger and execute worker
    """
    setup_logger(config.get("rabbitmq_logging"))
    arch_worker = RetimestampingWorker(config)
    arch_worker.run()
