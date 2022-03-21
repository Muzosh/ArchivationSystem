# from contextlib import closing - was unused
import random, string
from datetime import datetime
from archivingsystem.common.exceptions import (
    RecordDoesNotExistCustomException,
)

# from common.yaml_parser import parse_yaml_config - was unused
from archivingsystem.database.archived_file import ArchivedFile
from archivingsystem.database.db_library import (
    DatabaseHandler,
    MysqlConnection,
)
from archivingsystem.database.file_package import FilePackage


def main():
    db_config = {
        "user": "ncadmin",
        "password": "ncadmin",
        "host": "127.0.0.1",
        "database": "archivingsystem",
    }
    with MysqlConnection(db_config) as db_connection:
        db_handler = DatabaseHandler(db_connection)

        new_file_id = None
        new_owner = "".join(
            random.choices(
                string.ascii_uppercase
                + string.ascii_lowercase
                + string.digits,
                k=12,
            )
        )

        try:
            all_file_id = db_handler.get_all_file_id()

            last_archived_file: ArchivedFile = (
                db_handler.get_specific_archived_file_record_by_file_id(
                    all_file_id[-1]
                )
            )
        except RecordDoesNotExistCustomException:
            new_file_id = 1
            new_owner = "1"

        rec1 = ArchivedFile(
            column_data={
                "FileID": None,
                "FileName": "test_db.py",
                "OwnerName": new_owner,
                "OriginalFilePath": "/bla/bla/XY.txt",
                "PackageStoragePath": "/bla2/bla2/XY.pkg",
                "OriginFileHashSha512": b"thisistestbytesequence",
                "TimeOfFirstTS": datetime.now(),
                "ExpirationDateTS": datetime(2022, 12, 2),
                "SigningCert": b"test1",
                "SignatureHashSha512": b"test2",
                "Package0HashSha512": b"test3",
            }
        )

        db_handler.create_new_record_archived_file(rec1)

        last_archived_file: ArchivedFile = (
            db_handler.get_specific_archived_file_record_by_file_id(
                db_handler.get_all_file_id()[-1]
            )
        )

        rec2 = FilePackage(
            column_data={
                "PackageID": None,
                "ArchivedFileID": last_archived_file.FileID,
                "TimeStampingAuthority": "TS NAME 1",
                "IssuingDate": datetime.now(),
                "TsaCert": b"test1",
                "PackageHashSha512": b"d1c2e12cfeababc8b95daf6902e210b170992e68fd1c1f19565a40cf0099c6e2cb559b85d7c14ea05b4dca0a790656d003ccade9286827cffdf8e664fd271499",
            }
        )

        rec3 = FilePackage(
            column_data={
                "PackageID": None,
                "ArchivedFileID": last_archived_file.FileID,
                "TimeStampingAuthority": "TS NAME 2",
                "IssuingDate": datetime.now(),
                "TsaCert": b"test2",
                "PackageHashSha512": b"d1c2e12cfeababc8b95daf6902e210b170992e68fd1c1f19565a40cf0099c6e2cb559b85d7c14ea05b4dca0a790656d003ccade9286827cffdf8e664fd271499",
            }
        )

        db_handler.create_new_record_file_package(rec2)
        db_handler.create_new_record_file_package(rec3)

        created_rec: ArchivedFile = (
            db_handler.get_specific_archived_file_record_by_file_id(
                last_archived_file.FileID
            )
        )

        assert created_rec.ExpirationDateTS == datetime(
            rec1.ExpirationDateTS.year,
            rec1.ExpirationDateTS.month,
            rec1.ExpirationDateTS.day,
            rec1.ExpirationDateTS.hour,
            rec1.ExpirationDateTS.minute,
            rec1.ExpirationDateTS.second,
        )

        test_date = datetime.now()
        db_handler.update_expiration_date_ts(
            last_archived_file.FileID, test_date
        )

        assert db_handler.get_specific_archived_file_record_by_file_id(
            last_archived_file.FileID
        ).ExpirationDateTS == datetime(
            test_date.year,
            test_date.month,
            test_date.day,
            test_date.hour,
            test_date.minute,
            test_date.second,
        )

        id = db_handler.get_file_id_archived_file_rec(
            "test_db.py", last_archived_file.OwnerName
        )

        assert id == last_archived_file.FileID

        package_records = db_handler.get_file_package_records(
            last_archived_file.FileID, latest=False
        )

        assert isinstance(package_records, list) and len(package_records) == 2

        recs = db_handler.get_records_by_file_id(
            last_archived_file.FileID, latest=False
        )

        assert (
            isinstance(recs, tuple)
            and len(recs) == 2
            and isinstance(recs[1], list)
            and len(recs[1]) == 2
        )

        print("finished successfully")


if __name__ == "__main__":
    main()
