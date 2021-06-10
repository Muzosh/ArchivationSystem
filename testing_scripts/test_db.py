# from contextlib import closing - was unused
from datetime import datetime

# from common.yaml_parser import parse_yaml_config - was unused
from database.db_library import DatabaseLibrary, MysqlConnection
from database.table_classes.archivation_file import ArchivedFile
from database.table_classes.file_package import FilePackage


def main():
    db_config = {
        "user": "test_user",
        "password": "Password1",
        "host": "127.0.0.1",
        "database": "archivation_system_db",
    }
    with MysqlConnection(db_config) as db_connection:
        db_api = DatabaseLibrary(db_connection)
        rec1 = ArchivedFile(
            column_data={
                "FileID": None,
                "FileName": "XY2.txt",
                "OwnerName": "BLA3",
                "OriginalFilePath": "/bla/bla/XY.txt",
                "PackageStoragePath": "/bla2/bla2/XY.pkg",
                "OriginFileHashSha512": "d1c2e12cfeababc8b95daf6902e210b170992e68fd1c1f19565a40cf0099c6e2cb559b85d7c14ea05b4dca0a790656d003ccade9286827cffdf8e664fd271499",
                "TimeOfFirstTS": datetime.now(),
                "ExpirationDateTS": datetime(2022, 12, 2),
            }
        )

        db_api.create_new_record_archived_file(rec1)

        a = db_api.get_all_file_id()
        print(a)

        rec2 = FilePackage(
            column_data={
                "PackageID": None,
                "ArchivedFileID": a[0],
                "CertificationAuthority": "CA",
                "TimeStampingAuthority": "TS NAME",
                "AlgorithmTS": "SHAAAA",
                "AlgorithmSign": "BLAAA",
                "IssuingDate": datetime.now(),
                "ValidityLength": 3,
                "PackageHashSha512": "d1c2e12cfeababc8b95daf6902e210b170992e68fd1c1f19565a40cf0099c6e2cb559b85d7c14ea05b4dca0a790656d003ccade9286827cffdf8e664fd271499",
            }
        )

        db_api.create_new_record_file_package(rec2)

        # created_rec = db_api.get_specific_ArchivedFile_record_by_FileId(2)

        # db_api.update_expiration_date_specific_record(2, time)

        x = db_api.get_file_id_archived_file_rec("JA", "XY.txt")
        print("record id = ", x)

        fp = db_api.get_file_package_records(2, latest=False)
        # db_api.get_FilePackages_records(0, latest= True)

        recs = db_api.get_records_by_file_id(2)

        print(recs)


if __name__ == "__main__":
    main()


"""
    RECORD_ALREADY_EXIST - what it throws??
    test logging
"""
