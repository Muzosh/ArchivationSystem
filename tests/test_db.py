# from contextlib import closing - was unused
from datetime import datetime

# from common.yaml_parser import parse_yaml_config - was unused
from archivationsystem.database.archived_file import ArchivedFile
from archivationsystem.database.db_library import (
    DatabaseLibrary,
    MysqlConnection,
)
from archivationsystem.database.file_package import FilePackage


def main():
    db_config = {
        "user": "ncadmin",
        "password": "ncadmin",
        "host": "127.0.0.1",
        "database": "archivationsystem",
    }
    with MysqlConnection(db_config) as db_connection:
        db_api = DatabaseLibrary(db_connection)

        a = db_api.get_all_file_id()
        last_archive_file = (
            db_api.get_specific_archived_file_record_by_file_id(a[-1])
        )

        rec1 = ArchivedFile(
            column_data={
                "FileID": None,
                "FileName": "test/file.txt",
                "OwnerName": str(int(last_archive_file.OwnerName) + 1),
                "OriginalFilePath": "/bla/bla/XY.txt",
                "PackageStoragePath": "/bla2/bla2/XY.pkg",
                "OriginFileHashSha512": b"d1c2e12cfeababc8b95daf6902e210b170992e68fd1c1f19565a40cf0099c6e2cb559b85d7c14ea05b4dca0a790656d003ccade9286827cffdf8e664fd271499",
                "TimeOfFirstTS": datetime.now(),
                "ExpirationDateTS": datetime(2022, 12, 2),
                "SigningCert": b"test1",
                "SignatureHashSha512": b"test2",
                "Package0HashSha512": b"test3",
            }
        )

        db_api.create_new_record_archived_file(rec1)

        print(a)

        rec2 = FilePackage(
            column_data={
                "PackageID": 56,
                "ArchivedFileID": last_archive_file.ArchivedFileID,
                "TimeStampingAuthority": "TS NAME",
                "IssuingDate": datetime.now(),
                "TsaCert": b"test1",
                "PackageHashSha512": b"d1c2e12cfeababc8b95daf6902e210b170992e68fd1c1f19565a40cf0099c6e2cb559b85d7c14ea05b4dca0a790656d003ccade9286827cffdf8e664fd271499",
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
