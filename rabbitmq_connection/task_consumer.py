import logging
logger = logging.getLogger('Archivation System')

import pika
import ssl
import functools
import threading
from uuid import uuid4
from pika.credentials import PlainCredentials

class Connection_maker(object):
    """
    Object responsible for creating connection
    to rabbitmq server with given paramaters from config
    It will create connection via ssl if needed configuration
    values will be provided. If you dont need ssl connection 
    jus put false in config on plase of enable_ssl
    """
    def __init__(self, connection_config:dict):
        self.config = connection_config
        self.__host = None
        self.__virtual_host = None
        self.__port = None
        self.__credentials:dict = None
        self.__enable_ssl = None
    
    def __set_config_values(self):
        """
        parse all config values for creating a session
        host 
        virtual_host
        port
        credentials: 
            name
            password
        enable_ssl: { 
            Server_name_id: str
            certificate_file: str-path
            private_key_file: str-path
            pk_password: str
            CA_file: str-path
            CA_path: str-path
            CA_data: str-path
        } //or false
        """
        logger.debug("[rabbimq_connection_maker] mapping values from config")
        self.__host = self.config.get("host")
        self.__virtual_host = self.config.get("virtual_host")
        self.__port = self.config.get("port")
        self.__credentials:dict = self.config.get("credentials")
        self.__enable_ssl = self.config.get("enable_ssl")
    
    def __set_credentials(self):
        return PlainCredentials(
            self.__credentials.get('name'),
            self.__credentials.get('password'),
            erase_on_connect=True
        )

    def __setup_ssl(self):
        logger.debug("[rabbimq_connection_maker] setting up ssl configuration")
        if self.__enable_ssl is False:
            return None
        ssl_context = ssl.create_default_context(
            cafile= self.__enable_ssl.get('CA_file'),
            capath= self.__enable_ssl.get('CA_path'),
            cadata= self.__enable_ssl.get('CA_data')
        )
        ssl_context.load_cert_chain(
            certfile= self.__enable_ssl.get('certificate_file'),
            keyfile= self.__enable_ssl.get('private_key_file'),
            password= self.__enable_ssl.get('pk_password')
        )
        return pika.SSLOptions(
            ssl_context, self.__enable_ssl.get('Server_name_id')
        )

    def make_connection(self):
        """
        Method that will create rabbitmq connection
        """
        logger.info("[rabbimq_connection_maker] starting attempt to create connection to rabbitmq")
        self.__set_config_values()
        logger.debug("[rabbimq_connection_maker] setting values from config to connection parameter")
        connection_values = pika.ConnectionParameters(
            host= self.__host,
            port= self.__port,
            virtual_host= self.__virtual_host,
            credentials= self.__set_credentials(),
            ssl_options=  self.__setup_ssl() if self.__enable_ssl else None
        )
        logger.debug("[rabbimq_connection_maker] creating blocking connection")
        return pika.BlockingConnection(connection_values)
        



class Task_consumer(object):
    """
    Task consumer is responsible for listning on rabbitmq
    queue in channel for possible tasks. If task is recieved
    it  has to execute callback function which must be set
    before starting consuming. It will execute task in separated
    thread
    """
    def __init__(self, rabbitmq_connection:Connection_maker, channel_config:dict):
        self.connection = rabbitmq_connection.make_connection()
        self.rabbitmq_channel = self.connection.channel()
        self.consumer_ID = channel_config['consumer_ID']
        self.task_queue = channel_config['task_queue']
        self.control_exchange = channel_config['control_exchange']
        self.callback_setup = False

    def _setup_control_channel(self):
        logger.debug("[consumer] setting control exchange")
        self.rabbitmq_channel.queue_declare(self.consumer_ID)
        self.rabbitmq_channel.queue_bind(
            queue=self.consumer_ID,
            exchange=self.control_exchange,
            routing_key=self.consumer_ID
        )
        self.rabbitmq_channel.basic_consume(
            queue=self.consumer_ID,
            on_message_callback=self.__control_close
        )

    def set_callback(self, callback_function):
        """
        Function for setting callback function
        """
        logger.debug("[consumer] setting function to execute for given task")
        self.main_function = callback_function
        logger.debug("[consumer] setting task queue and callback function")
        self.rabbitmq_channel.basic_consume(
            queue=self.task_queue,
            on_message_callback=self.__callback_func
        )
        self.callback_setup = True

    def start(self):
        """
        This function will start consumer.
        Callback fucntion must be set before !!
        """
        self._setup_control_channel()
        if self.callback_setup is False:
            logger.Exception("[consumer] task queue and callback function havent been set up")
            raise Exception("Function for task has not been set up") 
        logger.info("[consumer] Starting to consume on channel")
        self.rabbitmq_channel.start_consuming()

    def close(self):
        logger.info("[consumer] closing consumer")
        self.rabbitmq_channel.stop_consuming()
        self.rabbitmq_channel.close()


    def __control_close(self, ch, method, properties, body):
        """
        body should contain shutdown command
        {
            control_command: shutdown
        }
        """
        logger.debug("[consumer] control message received")
        if body.get('control_command') == 'shutdown':
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self.close()
        else:
            logger.warning("[consumer] unknown control command")


    def __callback_func(self, ch, method, properties, body):
        threaded_job = threading.Thread(
            target=self.__threaded_func,
            args=(ch, method, body),
            daemon=True
        )
        logger.info("[consumer] creating thread for callback function")
        threaded_job.start()
        

    def __threaded_func(self, ch, method, body):
        """
        Function where callback function is executed
        It cathes unknown exceptions and logging them
        If callback function returns result with OK or
        KNOWN_ERROR(error which wasnt caused by fault in program),
        it will send task acknowledgment. If there will
        be exception that is caused by worker task wont
        be acknowledge and it will be consumed again by
        another worker
        """
        logger.info("[consumer] executing callback function")
        result = None
        try:
            result = self.main_function(body)
        except Exception as e:
            logger.exception("Exception occured in worker, not fault by task", exc_info=True, stack_info= True)
            result = None
        logger.info("[consumer] callback function finished")
        logger.info("[consumer] sending task acknowledgment")
        if result == "OK" or result == "KNOWN_ERROR":
            ack_callback = functools.partial(
                self.__send_ack_threadsafe, 
                ch, method.delivery_tag
                )
            self.connection.add_callback_threadsafe(
               ack_callback    
            )
        else: 
            logger.warning("[consumer] Operation failed")
            nack_callback = functools.partial(
                self.__send_nack_threadsafe, 
                ch, method.delivery_tag, body
            )
            logger.info("[consumer] rejecting task")
            self.connection.add_callback_threadsafe(
               nack_callback    
            )
            return

    def __send_ack_threadsafe(self, channel, delivery_tag):
        if channel.is_open and delivery_tag is not None:
            channel.basic_ack(delivery_tag=delivery_tag)
    
    def __send_nack_threadsafe(self, channel, delivery_tag, body):
        if channel.is_open and delivery_tag is not None:
            channel.basic_publish(
                exchange='',
                routing_key= 'failed_tasks',
                properties= pika.BasicProperties(correlation_id=str(uuid4)),
                body=body
            )
            channel.basic_ack(delivery_tag=delivery_tag)
