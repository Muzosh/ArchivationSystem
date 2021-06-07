

class DB_API_EXCEPTIONS(Exception):
   """
   Wrapps all exceptions from module db_library
   """
   pass
 
class RECORD_DOESNT_EXIST(DB_API_EXCEPTIONS):
   "given record doesnt exist in database"
   pass

class RECORD_CANNOT_BE_INSERTED(DB_API_EXCEPTIONS):
   "given record  cannot be inserted into database"
   pass

class DATABASE_SYNTAX_ERROR(DB_API_EXCEPTIONS):
   """
   Wrapps all syntax exceptions from Database 
   """
   pass

class DATABASE_ERROR(DB_API_EXCEPTIONS):
   """
   Wrapps all function exceptions from Database 
   """
   pass

class WRONG_RECORD_FORMAT(DB_API_EXCEPTIONS):
   """
   Data in record object doesnt have correct format for db insert
   """
   pass



class WorkerExceptions(Exception):
   """
   Wrapps all exceptions from workers
   """
   pass


class WrongTaskError(WorkerExceptions):
   """
   Raised when task body is not containing correct information
   or is not for correct worker
   """
   pass

class ArchivationOperationsError(Exception):
   """
   Wrapps all exceptions during archiving, retimestamping or validating
   """
   pass


class FileTransferWasntSuccesfullError(ArchivationOperationsError):
   """
   Raised when there was error during sftp transfer of files
   """
   pass


class RemoteTimemperError(ArchivationOperationsError):
   """
   Raised when remote timestamping authority cannot be reached
   """
   pass

class ArchivedFileNotValidError(ArchivationOperationsError):
   """
   Raised when validation of archivated file wasnt successful
   """
   pass

class OriginalFileNotValidError(ArchivationOperationsError):
   """
   Raised when archivated file and original file is no longer same
   """
   pass

class WrongPathToArchivatedFileError(ArchivationOperationsError):
   """
   Raised when path to archivated file is incorrect
   """
   pass

class TimestampInvalid(ArchivationOperationsError):
   """
   Raised when timestamp is not valid
   """
   pass

class DigestsNotMatchedError(ArchivationOperationsError):
   """
   Raised when 2 digests should matched but they dont
   """
   pass

class FileNotInDirectoryError(ArchivationOperationsError):
   """
   Raised when file is not in directory in
   which it should be
   """
   pass

class CertificateNotValidError(ArchivationOperationsError):
   """
   Raised when certificates are not same
   """
   pass

class UnableToGetRemoteFileDigest(ArchivationOperationsError):
   """
   Raised when there is problem to get remote file digest
   """
   pass