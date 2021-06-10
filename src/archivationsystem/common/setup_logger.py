import logging

from python_logging_rabbitmq import RabbitMQHandlerOneWay


def setup_logger(config: dict):
    logger = logging.getLogger("Archivation System")
    logger.addHandler(
        RabbitMQHandlerOneWay(
            host=config.get("host"),
            port=config.get("port"),
            username=config.get("username"),
            password=config.get("password"),
        )
    )
    logger.setLevel(config.get("logging_level"))
