import logging
logger = logging.getLogger('Archivation System')
from pathlib import Path, PurePath
from datetime import datetime
from common.exceptions import WRONG_RECORD_FORMAT

class File_package(object):
    def __init__(self, column_data = None):
        self.c_data = column_data
        self.PackageID = None
        self.ArchivatedFileID = None
        self.TimeStampingAuthority = None
        self.IssuingDate = None
        self.TsaCert = None
        self.PackageHashSha512 = None
        if self.c_data is not None:
            self.map_columns()

    def map_columns(self):
        self.PackageID = self.c_data['PackageID']
        self.ArchivatedFileID = self.c_data['ArchivatedFileID'] #INT
        self.TimeStampingAuthority = self.c_data['TimeStampingAuthority'] #STR
        self.IssuingDate = self.c_data['IssuingDate'] #DATETIME
        self.TsaCert = self.c_data['TsaCert']
        self.PackageHashSha512 = self.c_data['PackageHashSha512'] # BINARY - BYTES
        self.validate_columns()

    def validate_columns(self):
        errornous_columns = False
        logger.debug("[db_record] starting validation of record")

        if not isinstance(self.ArchivatedFileID, int):
            logger.exception(
                "[db_record] wrong type of ArchivatedFileID: %s",
                str(type(self.ArchivatedFileID))
                )
            errornous_columns = True 
        if not isinstance(self.TimeStampingAuthority, str):
            logger.exception("[db_record] wrong type of Time Stamping authority: %s",
                str(type(self.TimeStampingAuthority))
                )
            errornous_columns = True
        if not isinstance(self.IssuingDate, datetime): 
            logger.exception(
                "[db_record] wrong type of IssuingDate: %s",
                str(type(self.IssuingDate))
                )
        if not isinstance(self.TsaCert, bytes):
            logger.exception("[db_record] wrong type of TsaCert: %s",
                str(type(self.TsaCert))
                )
            errornous_columns = True 

        if not isinstance(self.PackageHashSha512, bytes):
            logger.exception("[db_record] wrong type of PackageHashSha512: %s",
                str(type(self.PackageHashSha512))
                )
            errornous_columns = True 
        
        if errornous_columns == True:
            raise WRONG_RECORD_FORMAT(" Wrong format of values in object --> cannot be inserted into DB") 

 