import base64
import logging
import os
import tarfile
from hashlib import sha512

import rfc3161ng
from common.exceptions import (
    DigestsNotMatchedError,
    FileNotInDirectoryError,
    TimestampInvalid,
)
from common.utils import (
    copy_file_to_dir,
    create_new_dir_in_location,
    create_tar_file_from_dir,
    get_certificate,
    get_current_crl,
    get_timestamp,
    hash_file,
    store_ts_data,
    validate_certificate,
    verify_timestamp,
)
from cryptography.hazmat.primitives.serialization import Encoding
from database.table_classes.file_package import FilePackage

logger = logging.getLogger("Archivation System")


class Retimestamper:
    """
    Retimestamper class is providing functionality
    for retimestamping proces of archived file


    on init it needs database library object and
    configuration file. Example could be found
    in example_config&files and it retimestamping_info part
    """

    def __init__(self, db_lib, config: dict):
        self.db_lib = db_lib
        self.config = config
        self.file_pack_record = FilePackage()

    def retimestamp(self, file_id):
        """
        Retimestamp function need file id from database
        of archived file which will be retimestamped
        """
        (
            storage_dir,
            actual_package_hash,
            pack_id,
        ) = self._verify_existing_package(file_id)
        ts_new = self._create_new_timestamp(storage_dir, actual_package_hash)
        tar_path = create_tar_file_from_dir(
            storage_dir,
            os.path.join(storage_dir, "PackageF{}.tar".format(pack_id)),
        )
        self._fill_package_record(file_id, ts_new, tar_path)

        logger.info(
            "[retimestamping] updating archived record with latest"
            " expiration date"
        )
        self.db_lib.update_expiration_date_specific_record(
            file_id, self._get_expiration_date(ts_new)
        )
        logger.info(
            "[retimestamping] inserting file package record into database"
        )
        self.db_lib.create_new_record_FilePackages(self.file_pack_record)
        return "OK"  # or exception

    def _verify_existing_package(self, file_id):
        logger.info("[retimestamping] verifying last package timestamp...")
        logger.debug(
            "[retimestamping] getting arichivated file record from db"
        )
        arch_f = self.db_lib.get_specific_ArchivedFile_record_by_FileId(
            file_id
        )
        logger.debug(
            "[retimestamping] getting latest package file record from db"
        )
        latest_file_p = self.db_lib.get_FilePackages_records(
            file_id, latest=True
        )
        storage_dir = arch_f.PackageStoragePath
        logger.debug("[retimestamping] getting data from package")
        ts, data, tar_package_path = self._get_ts_data_from_package(
            storage_dir
        )
        actual_package_hash = hash_file(sha512, tar_package_path)

        logger.debug(
            "[retimestamping] verifying latest package hashes with db record"
        )
        self._verify_final_package_hashes(
            latest_file_p.PackageHashSha512, actual_package_hash
        )
        logger.debug("[retimestamping] verifying latest timestamp")
        val = verify_timestamp(ts, data, self.config["TSA_info"])
        if val is not True:
            logger.exception(
                "[retimestamping] Last timestamp of package in path %s is"
                " invalid",
                str(storage_dir),
            )
            raise TimestampInvalid("Last timestamp of package is invalid")
        logger.info(
            "[retimestamping] last package timestamp has been succesfuly"
            " validated"
        )
        return storage_dir, actual_package_hash, latest_file_p.PackageID

    def _create_new_timestamp(self, storage_dir, actual_package_hash):
        logger.info("[retimestamping] getting new package timestamp")
        ts_new = get_timestamp(self.config["TSA_info"], actual_package_hash)
        logger.info(
            "[retimestamping] storing timestamp to storage directory.."
        )
        store_ts_data(ts_new, storage_dir, "timestamp")
        self._store_used_cert_files(storage_dir)
        return ts_new

    def _fill_package_record(self, file_id, ts_new, tar_path):
        logger.info(
            "[retimestamping] Filling new file package record with gathered"
            " data"
        )
        self.file_pack_record.ArchivedFileID = file_id
        self.file_pack_record.TimeStampingAuthority = self.config["TSA_info"][
            "url"
        ]
        self.file_pack_record.IssuingDate = rfc3161ng.get_timestamp(ts_new)
        cert = get_certificate(self.config["TSA_info"]["tsa_cert_path"])
        self.file_pack_record.TsaCert = base64.b64encode(
            cert.public_bytes(Encoding.PEM)
        )
        self.file_pack_record.PackageHashSha512 = hash_file(sha512, tar_path)
        logger.info("[retimestamping] File package record filled")

    def _get_ts_data_from_package(self, dir_path):
        files_in_dir = os.listdir(dir_path)
        package_name = list(
            filter(lambda x: x.startswith("Package"), files_in_dir)
        )
        if len(package_name) == 0:
            logger.exception(
                "[retimestamping] unable to find package in directory: %s",
                str(dir_path),
            )
            raise FileNotInDirectoryError(
                "directory doesnt have files which shoud be there."
            )
        tar_package_path = os.path.join(dir_path, package_name[0])
        logger.debug(
            "[retimestamping] getting data from tar file on path %s",
            str(tar_package_path),
        )
        with tarfile.open(tar_package_path, "r:") as tarf:
            names = tarf.getnames()
            ts = self._read_timestamp_from_tar(names, tarf)
            hash_f = self._hash_file_within_tar(sha512, tarf, names)
        logger.debug(
            "[retimestamping] needed data from tar package have been"
            " succesfuly retrieved"
        )
        return ts, hash_f, tar_package_path

    def _get_expiration_date(self, ts):
        years = self.config["validity_length"]
        time = rfc3161ng.get_timestamp(ts)
        logger.debug(
            "[retimestamping] expiration date setup from: %s + %s years",
            str(time),
            str(years),
        )
        return time.replace(year=time.year + years)

    def _get_timestamped_file_name(self, names):
        signature = list(filter(lambda x: x.startswith("signature"), names))
        if len(signature) != 0:
            logger.debug(
                "[retimestamping] Find timestamped file name in name, %s",
                str(signature),
            )
            return signature[0]
        package = list(filter(lambda x: x.startswith("Package"), names))
        if len(package) != 0:
            logger.debug(
                "[retimestamping] Find timestamped file name in name, %s",
                str(signature),
            )
            return package[0]
        logger.exception(
            "[retimestamping] Tar package doesnt have files which shoud be"
            " there. Tar Content: %s",
            str(names),
        )
        raise FileNotInDirectoryError(
            "Tar package doesnt have files which shoud be there."
        )

    def _store_used_cert_files(self, storage_dir):
        logger.debug(
            "[retimestamping] storing used certificate files to directory: %s",
            str(storage_dir),
        )
        dir_path = create_new_dir_in_location(storage_dir, "certificate_files")
        path_tsa_cert = self.config["TSA_info"]["tsa_cert_path"]
        path_tsa_ca_pem = self.config["TSA_info"]["tsa_ca_pem"]
        tsa_crl_url = self.config["TSA_info"]["tsa_crl_url"]
        copy_file_to_dir(path_tsa_cert, dir_path, "tsa_cert.crt")
        copy_file_to_dir(path_tsa_ca_pem, dir_path, "tsa_ca.pem")
        crl = get_current_crl(tsa_crl_url)
        validate_certificate(crl, path_tsa_ca_pem)
        store_ts_data(crl, dir_path, "tsa_cert_crl.crl")
        logger.debug(
            "[retimestamping] certificate files stored in dir of new package"
        )

    def _hash_file_within_tar(self, hash, tarf, names):
        f = tarf.extractfile(self._get_timestamped_file_name(names))
        file_hash = hash()
        buffer = f.read(8192)
        while buffer != b"":
            file_hash.update(buffer)
            buffer = f.read(8192)
        return file_hash.digest()

    def _read_timestamp_from_tar(self, names, tarf):
        logger.debug(
            "[retimestamping] trying to read timestamp from opened tar file"
        )
        ts_name = list(filter(lambda x: x.startswith("timestamp"), names))
        if len(ts_name) == 0:
            logger.debug(
                "[retimestamping] unable to find timestamp file in tarfile"
            )
            raise FileNotInDirectoryError(
                "[retimestamping] unable to find timestamp file in tarfile"
            )

        file = tarf.extractfile(ts_name[0])
        logger.debug("[retimestamping] reading timestamp from file")
        return file.read()

    def _verify_final_package_hashes(self, hash_db, hash_pack):
        logger.debug(
            "[retimestamping] hash from db: %s \n hash of origin file: %s",
            str(hash_db),
            str(hash_pack),
        )
        if hash_db != base64.b64encode(hash_pack):
            logger.warning(
                "[retimestamping] hashes of files do not match, verification"
                " of last timestamp wasnt succesffull"
            )
            raise DigestsNotMatchedError(
                "[retimestamping] hashes of files do not match, verification"
                " of last timestamp wasnt succesffull"
            )
        logger.info("[retimestamping] digests metched, files are the same")
