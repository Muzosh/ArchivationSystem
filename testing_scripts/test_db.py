from database.db_library import Mysql_connection, Database_Library
from database.table_classes.archivation_file import Archivated_file
from database.table_classes.file_package import File_package 
from common.yaml_parser import parse_yaml_config

from datetime import datetime

from contextlib import closing

def main():
    db_config = {
        'user' : 'test_user',
        'password' : 'Password1',
        'host' : '127.0.0.1',
        'database' : 'archivation_system_db'
    }
    with Mysql_connection(db_config) as db_connection:
        db_api = Database_Library(db_connection)
        rec1 = Archivated_file(
            column_data= {
            'FileID' : None,
            'FileName' : 'XY2.txt',
            'OwnerName' : 'BLA3',
            'OriginalFilePath' : '/bla/bla/XY.txt',
            'PackageStoragePath' : '/bla2/bla2/XY.pkg',
            'OriginFileHashSha512' : 'd1c2e12cfeababc8b95daf6902e210b170992e68fd1c1f19565a40cf0099c6e2cb559b85d7c14ea05b4dca0a790656d003ccade9286827cffdf8e664fd271499',
            'TimeOfFirstTS' : datetime.now(),
            'ExpirationDateTS' : datetime(2022,12,2)
        }
        )

        db_api.create_new_record_ArchivatedFiles(rec1)
        
        a = db_api.get_all_filedIDs()
        print(a)


        rec2 = File_package(
            column_data={
            'PackageID' : None,
            'ArchivatedFileID' : a[0],
            'CertificationAuthority' : 'CA',
            'TimeStampingAuthority' : "TS NAME",
            'AlgorithmTS' : "SHAAAA",
            'AlgorithmSign' : "BLAAA",
            'IssuingDate' : datetime.now(),
            'ValidityLength' : 3,
            'PackageHashSha512' : 'd1c2e12cfeababc8b95daf6902e210b170992e68fd1c1f19565a40cf0099c6e2cb559b85d7c14ea05b4dca0a790656d003ccade9286827cffdf8e664fd271499'
            }
        )
        
        db_api.create_new_record_FilePackages(rec2)
        
     
        
        #created_rec = db_api.get_specific_ArchivatedFile_record_by_FileId(2)
        
        
        #db_api.update_expiration_date_specific_record(2, time)
        
        
        x = db_api.get_fileID_ArchivatedFile_rec('JA', 'XY.txt' )
        print('record id = ', x)
        
        fp = db_api.get_FilePackages_records(2, latest= False)
        #db_api.get_FilePackages_records(0, latest= True)

        recs = db_api.get_records_by_FileId(2)

        print(recs)

if __name__ == '__main__':
    main()



"""
    RECORD_ALREADY_EXIST - what it throws??
    test logging
"""