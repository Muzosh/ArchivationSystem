import base64
import logging
import os
import tarfile
from hashlib import sha512

import rfc3161ng
from cryptography.hazmat.primitives.serialization import Encoding

from ..common import utils as common_utils
from ..common.exceptions import (
    DigestsNotMatchedCustomException,
    FileNotInDirectoryCustomException,
    TimestampInvalidCustomException,
)
from ..database.file_package import FilePackage

logger = logging.getLogger("archiving_system_logging")


class Retimestamper:
    """
    Retimestamper class is providing functionality
    for retimestamping proces of archived file


    on init it needs database library object and
    configuration file. Example could be found
    in example_config and it retimestamping_info part
    """

    def __init__(self, db_handler, config: dict):
        self.db_handler = db_handler
        self.config = config
        self.file_pack_record = FilePackage()

    def retimestamp(self, file_id):
        """
        Retimestamp function need file id from database
        of archived file which will be retimestamped
        """
        (
            archiving_storage_path,
            current_package_hash,
            package_id,
        ) = self._verify_existing_package(file_id)
        new_timestamp = self._create_new_timestamp(
            archiving_storage_path, current_package_hash
        )
        tar_path = os.path.join(
            archiving_storage_path, "PackageF{}.tar".format(package_id)
        )
        common_utils.create_tar_file_from_dir(
            archiving_storage_path,
            tar_path,
        )
        self._fill_package_record(file_id, new_timestamp, tar_path)

        logger.info("updating archived record with latest expiration date")
        self.db_handler.update_expiration_date_ts(
            file_id, self._get_expiration_date(new_timestamp)
        )

        logger.info("inserting file package record into database")
        self.db_handler.create_new_record_file_package(self.file_pack_record)
        return "OK"  # or exception

    def _verify_existing_package(self, file_id):
        logger.info("verifying last package timestamp")

        logger.info("getting arichivated file record from db")
        archived_file = (
            self.db_handler.get_specific_archived_file_record_by_file_id(
                file_id
            )
        )
        archiving_storage_path = archived_file.PackageStoragePath

        logger.info("getting latest package file record from db")
        latest_file_package = self.db_handler.get_file_package_records(
            file_id, latest=True
        )

        logger.info("getting data from package")
        (
            timestamp,
            timestamped_file_hash,
            tar_package_path,
        ) = self._get_ts_data_from_package(archiving_storage_path)

        logger.info("verifying latest package hash")
        current_package_hash = common_utils.get_file_hash(
            sha512, tar_package_path
        )
        self._verify_final_package_hashes(
            latest_file_package.PackageHashSha512, current_package_hash
        )

        logger.info("verifying latest timestamp")
        verification_result = common_utils.verify_timestamp(
            timestamp, timestamped_file_hash, self.config["TSA_info"]
        )
        if verification_result is not True:
            logger.exception(
                "Last timestamp of package in path %s is invalid",
                str(archiving_storage_path),
            )
            raise TimestampInvalidCustomException(
                "Last timestamp of package is invalid"
            )
        return (
            archiving_storage_path,
            current_package_hash,
            latest_file_package.PackageID,
        )

    def _create_new_timestamp(
        self, archiving_storage_path, current_package_hash
    ):
        logger.info("getting new package timestamp")
        new_timestamp = common_utils.get_timestamp(
            self.config["TSA_info"], current_package_hash
        )
        logger.info("storing timestamp to storage directory..")
        common_utils.store_ts_data(
            new_timestamp, archiving_storage_path, "timestamp"
        )
        self._store_used_cert_files(archiving_storage_path)
        return new_timestamp

    def _fill_package_record(self, file_id, new_timestamp, tar_path):
        logger.info("Filling new file package record with gathered data")
        self.file_pack_record.ArchivedFileID = file_id
        self.file_pack_record.TimeStampingAuthority = self.config["TSA_info"][
            "tsa_tsr_url"
        ]
        self.file_pack_record.IssuingDate = rfc3161ng.get_timestamp(
            new_timestamp
        )
        cert = common_utils.get_certificate(
            self.config["TSA_info"]["tsa_cert_path"]
        )
        self.file_pack_record.TsaCert = base64.b64encode(
            cert.public_bytes(Encoding.PEM)
        )
        self.file_pack_record.PackageHashSha512 = common_utils.get_file_hash(
            sha512, tar_path
        )
        logger.info("File package record filled")

    def _get_ts_data_from_package(self, dir_path):
        files_in_dir = os.listdir(dir_path)
        package_name_list = list(
            filter(lambda x: x.startswith("Package"), files_in_dir)
        )
        if len(package_name_list) == 0:
            logger.exception(
                "unable to find package in directory: %s",
                str(dir_path),
            )
            raise FileNotInDirectoryCustomException(
                "unable to find package in directory: {}".format(str(dir_path))
            )
        tar_package_path = os.path.join(dir_path, package_name_list[0])

        logger.debug(
            "getting data from tar file on path %s",
            str(tar_package_path),
        )
        with tarfile.open(tar_package_path, "r:") as tarf:
            file_names = tarf.getnames()
            timestamp = self._read_timestamp_from_tar(file_names, tarf)
            hash_f = self._get_timestamped_file_hash(sha512, tarf, file_names)

        return timestamp, hash_f, tar_package_path

    def _get_expiration_date(self, timestamp):
        years = self.config["validity_length_in_years"]
        time = rfc3161ng.get_timestamp(timestamp)
        logger.debug(
            "expiration date setup from: %s + %s years",
            str(time),
            str(years),
        )
        return time.replace(year=time.year + years)

    def _get_timestamped_file_name(self, file_names):
        signature = list(
            filter(lambda x: x.startswith("signature"), file_names)
        )
        if len(signature) != 0:
            logger.debug(
                "Found timestamped file name %s",
                str(signature),
            )
            return signature[0]
        package = list(filter(lambda x: x.startswith("Package"), file_names))
        if len(package) != 0:
            logger.debug(
                "Find timestamped file name in name, %s",
                str(signature),
            )
            return package[0]
        logger.exception(
            "Cannot find signature or PackageF in directory: %s",
            str(file_names),
        )
        raise FileNotInDirectoryCustomException(
            "Cannot find signature or PackageF in directory: {}".format(
                str(file_names)
            ),
        )

    def _store_used_cert_files(self, archiving_storage_path):
        logger.debug(
            "storing used certificate files to directory: %s",
            str(archiving_storage_path),
        )
        dir_path = common_utils.create_new_dir_in_location(
            archiving_storage_path, "certificate_files"
        )
        path_tsa_cert = self.config["TSA_info"]["tsa_cert_path"]
        path_tsa_ca_pem = self.config["TSA_info"]["tsa_ca_pem"]
        tsa_crl_url = self.config["TSA_info"]["tsa_crl_url"]
        common_utils.copy_file_to_dir(path_tsa_cert, dir_path, "tsa_cert.crt")
        common_utils.copy_file_to_dir(
            path_tsa_ca_pem, dir_path, "tsa_ca_cert.pem"
        )
        crl = common_utils.get_current_crl(tsa_crl_url)
        common_utils.validate_certificate(crl, path_tsa_ca_pem)
        common_utils.store_ts_data(crl, dir_path, "tsa_cert_crl.crl")
        logger.debug("certificate files stored in dir of new package")

    def _get_timestamped_file_hash(self, hash, tarf, file_names):
        f = tarf.extractfile(self._get_timestamped_file_name(file_names))
        file_hash = hash()
        buffer = f.read(8192)
        while buffer != b"":
            file_hash.update(buffer)
            buffer = f.read(8192)
        return file_hash.digest()

    def _read_timestamp_from_tar(self, file_names, tarf):
        logger.info("trying to read timestamp from opened tar file")
        ts_name = list(filter(lambda x: x.startswith("timestamp"), file_names))
        if len(ts_name) == 0:
            logger.exception("unable to find timestamp file in tarfile")
            raise FileNotInDirectoryCustomException(
                "unable to find timestamp file in tarfile"
            )

        file = tarf.extractfile(ts_name[0])
        logger.info("reading timestamp from file")
        return file.read()

    def _verify_final_package_hashes(self, hash_db, hash_pack):
        logger.debug(
            "hash from db: %s \n hash of package file: %s",
            str(hash_db),
            str(hash_pack),
        )
        if hash_db != base64.b64encode(hash_pack):
            logger.warning(
                "hash from db and hash of package file do not match"
            )
            raise DigestsNotMatchedCustomException(
                "hash from db and hash of package file do not match"
            )
        logger.info("hash from db and hash of package file matched")
