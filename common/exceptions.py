class DbApiCustomException(Exception):
    """
    Wrapps all exceptions from module db_library
    """

    pass


class RecordDoesNotExistCustomException(DbApiCustomException):
    "Given record doesnt exist in database"
    pass


class RecordCanNotBeInsertedCustomException(DbApiCustomException):
    "given record  cannot be inserted into database"
    pass


class DatabaseSyntaxErrorCustomException(DbApiCustomException):
    """
    Wrapps all syntax exceptions from Database
    """

    pass


class DatabaseErrorCustomException(DbApiCustomException):
    """
    Wrapps all function exceptions from Database
    """

    pass


class WrongRecordFormatCustomException(DbApiCustomException):
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


class FileTransferWasntSuccesfullError(ArchivationOperationCustomException):
    """
    Raised when there was error during sftp transfer of files
    """

    pass


class RemoteTimemperError(ArchivationOperationCustomException):
    """
    Raised when remote timestamping authority cannot be reached
    """

    pass


class ArchivedFileNotValidError(ArchivationOperationCustomException):
    """
    Raised when validation of archived file wasnt successful
    """

    pass


class OriginalFileNotValidError(ArchivationOperationCustomException):
    """
    Raised when archived file and original file is no longer same
    """

    pass


class WrongPathToArchivedFileError(ArchivationOperationCustomException):
    """
    Raised when path to archived file is incorrect
    """

    pass


class TimestampInvalid(ArchivationOperationCustomException):
    """
    Raised when timestamp is not valid
    """

    pass


class DigestsNotMatchedError(ArchivationOperationCustomException):
    """
    Raised when 2 digests should matched but they dont
    """

    pass


class FileNotInDirectoryError(ArchivationOperationCustomException):
    """
    Raised when file is not in directory in
    which it should be
    """

    pass


class CertificateNotValidError(ArchivationOperationCustomException):
    """
    Raised when certificates are not same
    """

    pass


class UnableToGetRemoteFileDigest(ArchivationOperationCustomException):
    """
    Raised when there is problem to get remote file digest
    """

    pass
