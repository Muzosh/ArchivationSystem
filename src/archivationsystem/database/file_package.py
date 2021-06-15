import logging
from datetime import datetime

from ..common.exceptions import WrongRecordFormatCustomException

# from pathlib import Path, PurePath - was unused


logger = logging.getLogger("Archivation System")


class FilePackage(object):
    def __init__(self, column_data=None):
        self.c_data = column_data
        self.PackageID = None
        self.ArchivedFileID = None
        self.TimeStampingAuthority = None
        self.IssuingDate = None
        self.TsaCert = None
        self.PackageHashSha512 = None
        if self.c_data is not None:
            self.map_columns()

    def map_columns(self):
        self.PackageID = self.c_data["PackageID"]
        self.ArchivedFileID = self.c_data["ArchivedFileID"]  # INT
        self.TimeStampingAuthority = self.c_data[
            "TimeStampingAuthority"
        ]  # STR
        self.IssuingDate = self.c_data["IssuingDate"]  # DATETIME
        self.TsaCert = self.c_data["TsaCert"]
        self.PackageHashSha512 = self.c_data[
            "PackageHashSha512"
        ]  # BINARY - BYTES
        self.validate_columns()

    def validate_columns(self):
        error = False
        logger.debug("[db_record] starting validation of record")

        if not isinstance(self.ArchivedFileID, int):
            logger.exception(
                "[db_record] wrong type of ArchivedFileID: %s",
                str(type(self.ArchivedFileID)),
            )
            error = True
        if not isinstance(self.TimeStampingAuthority, str):
            logger.exception(
                "[db_record] wrong type of Time Stamping authority: %s",
                str(type(self.TimeStampingAuthority)),
            )
            error = True
        if not isinstance(self.IssuingDate, datetime):
            logger.exception(
                "[db_record] wrong type of IssuingDate: %s",
                str(type(self.IssuingDate)),
            )
        if not isinstance(self.TsaCert, bytes):
            logger.exception(
                "[db_record] wrong type of TsaCert: %s",
                str(type(self.TsaCert)),
            )
            error = True

        if not isinstance(self.PackageHashSha512, bytes):
            logger.exception(
                "[db_record] wrong type of PackageHashSha512: %s",
                str(type(self.PackageHashSha512)),
            )
            error = True

        if error is True:
            raise WrongRecordFormatCustomException(
                " Wrong format of values in object --> cannot be inserted"
                " into DB"
            )
