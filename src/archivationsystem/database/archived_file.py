import logging
from datetime import datetime

from ..common.exceptions import WrongRecordFormatCustomException

# from pathlib import Path, PurePath - was unused


logger = logging.getLogger("archivation_system_logging")


class ArchivedFile(object):
    def __init__(self, column_data=None):
        self.c_data = column_data
        self.FileID = None
        self.FileName = None
        self.OwnerName = None
        self.OriginalFilePath = None
        self.PackageStoragePath = None
        self.OriginFileHashSha512 = None
        self.TimeOfFirstTS = None

        self.SigningCert = None
        self.SignatureHashSha512 = None
        self.Package0HashSha512 = None

        self.ExpirationDateTS = None

        if self.c_data is not None:
            self.map_columns()

    def map_columns(self):
        self.FileID = self.c_data["FileID"]
        self.FileName = self.c_data["FileName"]  # STR
        self.OwnerName = self.c_data["OwnerName"]  # STR
        self.OriginalFilePath = self.c_data["OriginalFilePath"]  # STR
        self.PackageStoragePath = self.c_data["PackageStoragePath"]  # STR
        self.OriginFileHashSha512 = self.c_data[
            "OriginFileHashSha512"
        ]  # BYTES
        self.TimeOfFirstTS = self.c_data["TimeOfFirstTS"]  # DATETIME

        self.SigningCert = self.c_data["SigningCert"]  # bytes
        self.SignatureHashSha512 = self.c_data["SignatureHashSha512"]  # bytes
        self.Package0HashSha512 = self.c_data["Package0HashSha512"]  # bytes

        self.ExpirationDateTS = self.c_data["ExpirationDateTS"]  # DATETIME
        self.validate_columns()

    def validate_columns(self):
        error = False
        logger.debug("[ArchivedFile.validate_columns] starting validation")
        if not isinstance(self.FileName, str):
            logger.exception(
                "[ArchivedFile.validate_columns] wrong type of FileName: %s",
                str(type(self.FileName)),
            )
            error = True
        if not isinstance(self.OriginalFilePath, str):
            logger.exception(
                "[ArchivedFile.validate_columns] wrong type of"
                " OriginalFilePath: %s",
                str(type(self.OriginalFilePath)),
            )
            error = True
        if not isinstance(self.PackageStoragePath, str):
            logger.exception(
                "[ArchivedFile.validate_columns] wrong type of"
                " PackageStoragePath: %s",
                str(type(self.PackageStoragePath)),
            )
            error = True
        if not isinstance(self.OriginFileHashSha512, bytes):
            logger.exception(
                "[ArchivedFile.validate_columns] wrong type of"
                " OriginFileHashSha512: %s",
                str(type(self.OriginFileHashSha512)),
            )
            error = True
        if not isinstance(self.TimeOfFirstTS, datetime):
            logger.exception(
                "[ArchivedFile.validate_columns] wrong type of"
                " TimeOfFirstTS: %s",
                str(type(self.TimeOfFirstTS)),
            )
            error = True

        if not isinstance(self.SigningCert, bytes):
            logger.exception(
                "[ArchivedFile.validate_columns] wrong type of"
                " SigningCert: %s",
                str(type(self.SigningCert)),
            )
            error = True

        if not isinstance(self.SignatureHashSha512, bytes):
            logger.exception(
                "[ArchivedFile.validate_columns] wrong type of"
                " SignatureHashSha512: %s",
                str(type(self.SignatureHashSha512)),
            )
            error = True

        if not isinstance(self.Package0HashSha512, bytes):
            logger.exception(
                "[ArchivedFile.validate_columns] wrong type of"
                " Package0HashSha512: %s",
                str(type(self.Package0HashSha512)),
            )
            error = True

        if not isinstance(self.ExpirationDateTS, datetime):
            logger.exception(
                "[ArchivedFile.validate_columns] wrong type of"
                " ExpirationDateTS: %s",
                str(type(self.ExpirationDateTS)),
            )
            error = True

        if error is True:
            raise WrongRecordFormatCustomException(
                "Wrong format of values in object --> cannot be inserted"
                " into DB"
            )
