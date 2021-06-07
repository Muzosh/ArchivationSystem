import logging
logger = logging.getLogger('Archivation System')

from mysql.connector import MySQLConnection
from .table_classes.archivation_file import Archivated_file
from .table_classes.file_package import File_package
from typing import overload
from contextlib import closing
from datetime import datetime
import base64
from common.exceptions import RECORD_DOESNT_EXIST
from common.exception_wrappers import db_lib_exception_wrapper
from .sql_scripts.sql_queries import (
    QUERY_ALL_COLUMNS_ON_FILEID_ARCHIVATED_FILES,
    QUERY_FILEID_ON_FILENAME_OWNER_ARCHIVATED_FILES,
    QUERY_UPDATE_EXPIRATION_DATE_ARCHIVATED_FILES,
    QUERY_INSRET_INTO_ARCHIVATED_FILES,
    QUERY_INSRET_INTO_FILE_PACKAGES,
    QUERY_ALL_COLUMNS_ON_FILEID_FILE_PACKAGES,
    QUERY_ALL_COLUMNS_ON_FILEID_FILE_PACKAGES_TOP1,
    QUERY_SELECT_FILEID
)

class Mysql_connection(object):
    """
    This class is responsible for creating managed connection to database
    It takes argument config which has to be in format like:
    {
        'user' : 'user',
        'password' : 'password',
        'host': '127.0.0.1',
        ...
        more potentional parameters can be found here:
        https://dev.mysql.com/doc/connector-python/en/connector-python-connectargs.html
    }
    """
    def __init__(self, config:dict):
        self.config = config
        self.db_connection = None

    def __enter__(self):
        self.db_connection = MySQLConnection(**self.config) 
        return self.db_connection

    def __exit__(self, exc_type, exc_value, traceback):
        if self.db_connection is not None:
            self.db_connection.close()






class Database_Library(object):
    """
    database api library, responsible for querying and formating data from/to DB
    requires on initialization Mysql_connection 
    """
    def __init__(self, db_connection:Mysql_connection):
        self.db_connecton = db_connection

    @db_lib_exception_wrapper
    def get_all_filedIDs(self):
        """
        Retruns a list of fileIDs in DB
        """
        id_list = []
        ids = self._execute_select_query(QUERY_SELECT_FILEID)
        if len(ids) == 0:
            raise RECORD_DOESNT_EXIST("NO RECORD IDS")
        for id in ids:
            id_list.append(id[0])
        return id_list 

    @db_lib_exception_wrapper
    def update_expiration_date_specific_record(self, file_id, newDate:datetime):
        """
        It will update expiration date for specific record in table archivated files
        """
        self._execute_insert_query(
            self._get_fromated_query_update_expiration_date(
                file_id,
                newDate.strftime('%Y-%m-%d %H:%M:%S')
            )
        )

    @db_lib_exception_wrapper
    def add_full_records(self, archf_data:Archivated_file, filep_data:File_package):
        """
        This function is responsible for creating records of archived file in database
        """
        self.create_new_record_ArchivatedFiles(archf_data)
        filep_data.ArchivatedFileID = self.get_fileID_ArchivatedFile_rec(
            archf_data.OwnerName,
            archf_data.FileName
        )
        self.create_new_record_FilePackages(filep_data)

    @db_lib_exception_wrapper
    def create_new_record_ArchivatedFiles(self, archf_data:Archivated_file):
        """
        This will create new record in database for table ArchivatedFiles
        """
        self._execute_insert_query(
            self._get_formated_insert_query_ArchivatedFiles(archf_data)
        )

    @db_lib_exception_wrapper
    def create_new_record_FilePackages(self, filep_data:File_package):
        """
        This will create new record in database for table FilePackages.
        """
        self._execute_insert_query(
            self._get_fromated_query_insert_file_packages(filep_data)
        )

    @db_lib_exception_wrapper
    def get_records_by_FileId(self, file_id, latest = False):
        """
        Thiw function will gather data from ArchivatedFiles table
        and all(or optionaly latest) binded records from FilePackages. 
        The query is based on FileID,
        Optional argument latest is responsible for returning just latest
        returns: 
            record object of Archivated_file,
            list of obects of File_package 
        """
        return (
            self.get_specific_ArchivatedFile_record_by_FileId(file_id),
            self.get_FilePackages_records(file_id, latest)
        )
        

    @db_lib_exception_wrapper
    def get_specific_ArchivatedFile_record_by_FileId(self, file_id:int):
        """
        This will get data based on fileID from ArchivatedFiles table 
        return object of Archivated_file
        """

        record_values = self._execute_select_query(
            self._get_formated_query_record_archivated_files_by_fileID(
                file_id
            )
        )
        if len(record_values) == 0:
            raise RECORD_DOESNT_EXIST("NO RECORDS EXISTS FOR GIVEN FILEID") 
        return self.__get_archivated_files(record_values)[0]


    @db_lib_exception_wrapper
    def get_FilePackages_records(self, archivatedFileID:str, latest=False):
        """
        This method will get all FilePackage records from DB assinged
        under given FileID
        Optional argument latest is responsible for returning just latest
        record from table FilePackages
        return list with objects of File_package
        """
     
        if latest:
            query_f = self._get_fromated_query_select_all_c_file_package_TOP1
        else: 
            query_f = self._get_fromated_query_select_all_c_file_package

        records_values = self._execute_select_query(
            query_f(
                archivatedFileID
            )
        )
        if len(records_values) == 0:
            raise Exception("NO FILE PACKAGE RECORDS EXISTS FOR GIVEN ARCHIVATED_FILE ID")
        if latest:
            return self.__get_file_packages(records_values)[0]
        return self.__get_file_packages(records_values)

    @db_lib_exception_wrapper
    def get_fileID_ArchivatedFile_rec(self, owner_name:str, file_name:str):
        """
        This will return FileID of file that matches owner_name and file_name
        """
        results = self._execute_select_query(
            self._get_formated_query_based_on_FileName_owner(
                file_name, owner_name
            )
        )
        if len(results) == 0:
            raise Exception("NO RECORDS MATCHING GIVEN PARAMERTERS")
        return results[0][0]

    
    def _get_formated_insert_query_ArchivatedFiles(self, arch_f:Archivated_file):
        arch_f.validate_columns()
        return QUERY_INSRET_INTO_ARCHIVATED_FILES.format(
            arch_f.FileName,
            arch_f.OwnerName,
            str(arch_f.OriginalFilePath),
            str(arch_f.PackageStoragePath),
            repr(base64.b64encode(arch_f.OriginFileHashSha512))[1:],
            arch_f.TimeOfFirstTS.strftime('%Y-%m-%d %H:%M:%S'),
            repr(base64.b64encode(arch_f.SigningCert))[1:],
            repr(base64.b64encode(arch_f.SignatureHashSha512))[1:],
            repr(base64.b64encode(arch_f.Package0HashSha512))[1:], 
            arch_f.ExpirationDateTS.strftime('%Y-%m-%d %H:%M:%S')
        )
        
    
    def _get_formated_query_based_on_FileName_owner(self, file_name, owner_name):
        return QUERY_FILEID_ON_FILENAME_OWNER_ARCHIVATED_FILES.format(
            file_name,
            owner_name,
            )

    def _get_formated_query_record_archivated_files_by_fileID(self, file_id):
        return QUERY_ALL_COLUMNS_ON_FILEID_ARCHIVATED_FILES.format(
            file_id
        )

    def _get_fromated_query_update_expiration_date(self, file_id, date):
        return QUERY_UPDATE_EXPIRATION_DATE_ARCHIVATED_FILES.format(
            date,
            file_id
        )

    def _get_fromated_query_insert_file_packages(self, file_p: File_package):
        file_p.validate_columns()
        return QUERY_INSRET_INTO_FILE_PACKAGES.format(
            file_p.ArchivatedFileID,
            file_p.TimeStampingAuthority,
            file_p.IssuingDate.strftime('%Y-%m-%d %H:%M:%S'), 
            repr(base64.b64encode(file_p.TsaCert))[1:],
            repr(base64.b64encode(file_p.PackageHashSha512))[1:]
        )

    def _get_fromated_query_select_all_c_file_package(self, file_id):
        return QUERY_ALL_COLUMNS_ON_FILEID_FILE_PACKAGES.format(
            file_id
        )
    def _get_fromated_query_select_all_c_file_package_TOP1(self, file_id):
        return QUERY_ALL_COLUMNS_ON_FILEID_FILE_PACKAGES_TOP1.format(
            file_id
        )

    def _execute_select_query(self, query):
        with closing(self.db_connecton.cursor()) as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def _execute_insert_query(self, query):
        with closing(self.db_connecton.cursor()) as cursor:
            cursor.execute(query)
            self.db_connecton.commit()

    def __get_file_packages(self, data):
        list_File_packages = list()
        for column in data:
            list_File_packages.append(
                File_package(
                    self.__get_data_dictionary_for_file_package(
                        column
                    )
                )
            )
        return list_File_packages

    def __get_archivated_files(self, data):
        list_Archivated_files = list()
        for column in data:
            list_Archivated_files.append(
                Archivated_file(
                    self.__get_data_dictionary_for_archivated_file(
                        column
                    )
                )
            )
        return list_Archivated_files

    def __get_data_dictionary_for_archivated_file(self, column_data):
        return {
            'FileID' : column_data[0],
            'FileName' : column_data[1],
            'OwnerName' : column_data[2],
            'OriginalFilePath' : column_data[3],
            'PackageStoragePath' : column_data[4],
            'OriginFileHashSha512' : column_data[5],
            'TimeOfFirstTS' : column_data[6],
            'SigningCert': column_data[7],
            'SignatureHashSha512': column_data[8],
            'Package0HashSha512': column_data[9],
            'ExpirationDateTS' : column_data[10]
        }

    def __get_data_dictionary_for_file_package(self, column_data):
        return {
            'PackageID' : column_data[0],
            'ArchivatedFileID' : column_data[1],
            'TimeStampingAuthority' : column_data[2],
            'IssuingDate' : column_data[3],
            'TsaCert' : column_data[4],
            'PackageHashSha512' : column_data[5]
        }