import logging
from functools import wraps

from mysql.connector import errors as mysql_errors

from .exceptions import (
    ArchivationOperationCustomException,
    CertificateNotValidCustomException,
    DatabaseErrorCustomException,
    DatabaseSyntaxErrorCustomException,
    RecordCanNotBeInsertedCustomException,
    RecordDoesNotExistCustomException,
    WrongRecordFormatCustomException,
    WrongTaskCustomException,
)

# from requests.exceptions import ConnectionError - was unused


logger = logging.getLogger("archivation_system_logging")


def db_handler_exception_wrapper(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (mysql_errors.ProgrammingError) as e:
            logger.exception(
                "Wrong SQL syntax probably",
                exc_info=True,
                stack_info=True,
            )
            raise DatabaseSyntaxErrorCustomException(e) from e
        except (mysql_errors.IntegrityError) as e:
            logger.exception(
                "Record probably exist or other constraint failed",
                exc_info=True,
                stack_info=True,
            )
            raise RecordCanNotBeInsertedCustomException(e) from e
        except (
            RecordDoesNotExistCustomException,
            WrongRecordFormatCustomException,
        ) as e:
            logger.error("Incorrect use of db")
            raise e
        except (mysql_errors.Error) as e:
            logger.exception(
                "Some unhandled exception appeared in mysql.connector module",
                exc_info=True,
                stack_info=True,
            )
            raise DatabaseErrorCustomException(e) from e

    return wrapper


def task_exceptions_wrapper(function):
    """
    Catches exceptions after which task should be acknowledged
    and not repeated since there is not issue with worker
    but with input values
    """

    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except CertificateNotValidCustomException:  # as e: - was unused
            logger.exception(
                "Certificate is invalid",
                exc_info=True,
                stack_info=True,
            )
            result = "FAILED"
        except (ArchivationOperationCustomException):  # as e: - was unused
            logger.exception(
                "Exception occured during archivation, verification or"
                " timestamping process",
                exc_info=True,
                stack_info=True,
            )
            result = "FAILED"
        except (WrongTaskCustomException):  # as e: - was unused
            logger.exception(
                "Wrong task came for given worker",
                exc_info=True,
                stack_info=True,
            )
            result = "KNOWN_ERROR"
        except (RecordCanNotBeInsertedCustomException):  # as e: - was unused
            logger.exception(
                "Constraint error",
                exc_info=True,
                stack_info=True,
            )
            result = "FAILED"
        except (EOFError):  # as e: - was unused
            logger.exception(
                "File operation error",
                exc_info=True,
                stack_info=True,
            )
            result = "FAILED"
        return result

    return wrapper
