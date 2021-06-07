
import logging
logger = logging.getLogger('Archivation System')
from contextlib import closing
import json
from database.db_library import Mysql_connection, Database_Library
from common.setup_logger import setup_logger
from common.exceptions import WrongTaskError
from common.exception_wrappers import task_exceptions_wrapper
from rabbitmq_connection.task_consumer import Connection_maker, Task_consumer
from .retimestamper import Retimestamper


class Retimestamping_Worker():
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
        self.rmq_config =  config.get("rabbitmq_connection")
        self.connection = Connection_maker(self.rmq_config)
        self.task_consumer = Task_consumer(self.connection, config.get('rabbitmq_info'))
        self.task_consumer.set_callback(self.retimestamp)
        self.retimestamping_config = config.get("retimestamping_info")
        

    def run(self):
        logger.info("[retimestamping_worker] starting retimestamping worker consumer")
        self.task_consumer.start()

    @task_exceptions_wrapper
    def retimestamp(self, body):
        """
        Callback function which will be executed on task.
        It needs correct task body otherwise it will throw 
        WrongTask Exception
        """
        logger.info("[retimestamping_worker] recieved task with body: %s", str(body))

        logger.debug("[retimestamping_worker] creation of database connection")
        with Mysql_connection(self.db_config) as db_connection:
            db_lib = Database_Library(db_connection)
            retimestamper = Retimestamper(db_lib, self.retimestamping_config)
            file_id= self._parse_message_body(body)
            logger.info("[retimestamping_worker] executing retimestamping of file id: %s", str(file_id))
            result = retimestamper.retimestamp(file_id)
            logger.info("[retimestamping_worker] retimestamping was finished")
        return result

    def _parse_message_body(self,body):
        body = json.loads(body)
        if not body["task"] == "Retimestamp":
            logger.warning(
                "incorrect task label for retimestamping worker, body: %s",
                 str(body)
                 )
            raise WrongTaskError("task is not for this worker")
        file_id = body['file_id']
        return file_id

def run_worker(config):
    """
    This function will setup logger and execute worker
    """
    setup_logger(config.get('rabbitmq_logging'))
    arch_worker = Retimestamping_Worker(config)
    arch_worker.run()
