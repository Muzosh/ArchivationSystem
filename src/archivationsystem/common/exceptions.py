class DbHandlerCustomException(Exception):
    """
    Wrapps all exceptions from module db_handler
    """

    pass


class RecordDoesNotExistCustomException(DbHandlerCustomException):
    "Given record doesnt exist in database"
    pass


class RecordCanNotBeInsertedCustomException(DbHandlerCustomException):
    "given record  cannot be inserted into database"
    pass


class DatabaseSyntaxErrorCustomException(DbHandlerCustomException):
    """
    Wrapps all syntax exceptions from Database
    """

    pass


class DatabaseErrorCustomException(DbHandlerCustomException):
    """
    Wrapps all function exceptions from Database
    """

    pass


class WrongRecordFormatCustomException(DbHandlerCustomException):
    """
    Data in record object doesnt have correct format for db insert
    """

    pass


class WorkerCustomException(Exception):
    """
    Wrapps all exceptions from workers
    """

    pass


class WrongTaskCustomException(WorkerCustomException):
    """
    Raised when task body is not containing correct information
    or is not for correct worker
    """

    pass


class ArchivationOperationCustomException(Exception):
    """
    Wrapps all exceptions during archiving, retimestamping or validating
    """

    pass


class FileTransferNotSuccesfullCustomException(
    ArchivationOperationCustomException
):
    """
    Raised when there was error during sftp transfer of files
    """

    pass


class RemoteTimemperCustomException(ArchivationOperationCustomException):
    """
    Raised when remote timestamping authority cannot be reached
    """

    pass


class ArchivedFileNotValidCustomException(ArchivationOperationCustomException):
    """
    Raised when validation of archived file wasnt successful
    """

    pass


class OriginalFileNotValidError(ArchivationOperationCustomException):
    """
    Raised when archived file and original file is no longer same
    """

    pass


class WrongPathToArchivedFileCustomException(
    ArchivationOperationCustomException
):
    """
    Raised when path to archived file is incorrect
    """

    pass


class TimestampInvalidCustomException(ArchivationOperationCustomException):
    """
    Raised when timestamp is not valid
    """

    pass


class DigestsNotMatchedCustomException(ArchivationOperationCustomException):
    """
    Raised when 2 digests should matched but they dont
    """

    pass


class FileNotInDirectoryCustomException(ArchivationOperationCustomException):
    """
    Raised when file is not in directory in
    which it should be
    """

    pass


class CertificateNotValidCustomException(ArchivationOperationCustomException):
    """
    Raised when certificates are not same
    """

    pass


class UnableToGetRemoteFileDigestCustomException(
    ArchivationOperationCustomException
):
    """
    Raised when there is problem to get remote file digest
    """

    pass
