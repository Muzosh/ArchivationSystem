import logging
from functools import wraps

from mysql.connector import errors as mysql_errors

from .exceptions import (
    DatabaseErrorCustomException,
    DatabaseSyntaxErrorCustomException,
    RecordCanNotBeInsertedCustomException,
    RecordDoesNotExistCustomException,
    WrongRecordFormatCustomException,
    ArchivationOperationCustomException,
    CertificateNotValidError,
    WrongTaskCustomException,
)

# from requests.exceptions import ConnectionError - was unused


logger = logging.getLogger("Archivation System")


def db_lib_exception_wrapper(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (mysql_errors.ProgrammingError) as e:
            logger.exception(
                "[db_api] Wrong SQL syntax probably",
                exc_info=True,
                stack_info=True,
            )
            raise DatabaseSyntaxErrorCustomException(e) from e
        except (mysql_errors.IntegrityError) as e:
            logger.warning(
                "[db_api] Record probably exist or other constraint failed",
                exc_info=True,
                stack_info=True,
            )
            raise RecordCanNotBeInsertedCustomException(e) from e
        except (
            RecordDoesNotExistCustomException,
            WrongRecordFormatCustomException,
        ) as e:
            logger.warning("[db_api] Incorrect use of db")
            raise e
        except (mysql_errors.Error) as e:
            logger.exception(
                "[db_api] Some unhendled exception appeared in mysql.connector"
                " module",
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
        except (CertificateNotValidError):  # as e: - was unused
            logger.warning(
                "Certificate not valid", exc_info=True, stack_info=True
            )
            result = "FAILED"
        except (ArchivationOperationCustomException):  # as e: - was unused
            logger.warning(
                "Exception occured during archivation, verification or"
                " timestamping process",
                exc_info=True,
                stack_info=True,
            )
            result = "FAILED"
        except (WrongTaskCustomException):  # as e: - was unused
            logger.warning(
                "Wrong task came for given worker",
                exc_info=True,
                stack_info=True,
            )
            result = "KNOWN_ERROR"
        except (RecordCanNotBeInsertedCustomException):  # as e: - was unused
            logger.warning("Constraint error", exc_info=True, stack_info=True)
            result = "KNOWN_ERROR"
        except (EOFError):  # as e: - was unused
            logger.warning(
                "File operation error", exc_info=True, stack_info=True
            )
            result = "FAILED"
        return result

    return wrapper
