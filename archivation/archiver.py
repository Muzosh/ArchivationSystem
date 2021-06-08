import base64
import logging
import ntpath
import os
from contextlib import closing
from hashlib import sha512
from uuid import uuid4

import rfc3161ng
from common.exceptions import FileTransferWasntSuccesfullError
from common.utils import (
    copy_file_to_dir,
    create_new_dir_in_location,
    create_tar_file_from_dir,
    delete_file,
    get_certificate,
    get_current_crl,
    get_private_key,
    get_remote_hash,
    get_sftp_connection,
    get_timestamp,
    hash_file,
    sign_data,
    store_signature,
    store_ts_data,
    validate_certificate,
)
from cryptography.hazmat.primitives.serialization import Encoding
from database.table_classes.archivation_file import ArchivedFile
from database.table_classes.file_package import FilePackage

logger = logging.getLogger("Archivation System")


class Archiver:
    """
    Archiver class is providing functionality
    for archiving proces of file

    archive function should be called

    on init it needs database library object and
    configuration file. Example could be found
    in example_config&files and it needs archivation_system_info part
    """

    def __init__(self, db_lib, config: dict):
        self.db_lib = db_lib
        self.archivation_config = config
        self.archiveted_file_rec = ArchivedFile()
        self.file_pack_record = FilePackage()
        self.storage_dir = self.archivation_config.get("storage_dir_path")

    def archive(self, file_path, owner):
        """
        Method where archiving is called in steps
        it need file path to file which will be archived
        file could be localy or remotly...based on configuration recieved
        on object init

        and it needs original owner name
        """
        self._assign_original_data(file_path, owner)
        self._assign_tsa_info()
        self._validate_certificates()
        self._transfer_file(file_path)
        self._make_ts0()
        self._make_package0()
        self._sign_package()
        self._make_ts1()
        self._store_used_cert_files()
        self._make_final_package()

        self._insert_db_record()

        return "OK"  # or exception

    def _assign_original_data(self, file_path, owner):
        logger.info("[archivation] filling archivation data info")
        self.archiveted_file_rec.FileName = self._get_file_name(file_path)
        self.archiveted_file_rec.OwnerName = owner
        self.archiveted_file_rec.OriginalFilePath = file_path

    def _assign_tsa_info(self):
        logger.info("[archivation] filling TSA info to file package record")
        self.file_pack_record.TimeStampingAuthority = self.archivation_config[
            "TSA_info"
        ]["url"]
        cert = get_certificate(
            self.archivation_config["TSA_info"]["tsa_cert_path"]
        )
        self.file_pack_record.TsaCert = base64.b64encode(
            cert.public_bytes(Encoding.PEM)
        )

    def _validate_certificates(self):
        logger.info("validation certificates")
        path_ca = self.archivation_config["signing_info"]["certificate_path"]
        path_crl = self.archivation_config["signing_info"]["crl_path"]
        path_tsa_ca_pem = self.archivation_config["TSA_info"]["tsa_ca_pem"]
        tsa_crl_url = self.archivation_config["TSA_info"]["tsa_crl_url"]
        self.crl = get_current_crl(tsa_crl_url)
        validate_certificate(self.crl, path_tsa_ca_pem)
        logger.debug("TSA cert valid")
        with open(
            path_crl, "rb"
        ) as f:  # NOTE: comment if you dont want to use CRL
            crl_s = f.load()  # NOTE: comment if you dont want to use CRL
        validate_certificate(
            crl_s, path_tsa_ca_pem
        )  # NOTE: comment if you dont want to use CRL
        logger.debug("signing cert valid")

    def _transfer_file(self, file_path):
        if self.archivation_config["remote_access"] is False:
            logger.info(
                "[archivation] starting to transfer local file to archivation"
                " storage"
            )
            (
                self.archiveted_file_rec.PackageStoragePath,
                self.archiveted_file_rec.OriginFileHashSha512,
            ) = self._get_file(file_path)
        else:
            logger.info(
                "[archivation] starting to transfer remote file to archivation"
                " storage"
            )
            (
                self.archiveted_file_rec.PackageStoragePath,
                self.archiveted_file_rec.OriginFileHashSha512,
            ) = self._get_remote_file(file_path)
        logger.info("[archivation] validating data transfer")
        self._validate_data_transfer(
            self.archiveted_file_rec.OriginFileHashSha512, self.dst_file_path
        )
        logger.info("[archivation] data transfer completed succesfully")

    def _make_ts0(self):
        logger.info("[archivation] creating timestamp for original file")
        ts0 = self._timestamp_data(
            self.archiveted_file_rec.OriginFileHashSha512, "timestamp0"
        )
        self.archiveted_file_rec.TimeOfFirstTS = rfc3161ng.get_timestamp(ts0)
        logger.info("[archivation] timestamp recieved successfully")

    def _make_package0(self):
        logger.info("[archivation] packing timestamp0 and file to tar package")
        package0_tar_path = self._make_tar_package_from_dir_content(
            self.archiveted_file_rec.PackageStoragePath, "Package0.tar"
        )
        self.archiveted_file_rec.Package0HashSha512 = hash_file(
            sha512, package0_tar_path
        )
        logger.info("[archivation] package0 created successfully")

    def _sign_package(self):
        logger.info("[archivation] geting signature of hash of package0")
        signature = self.__make_signature(
            self.archiveted_file_rec.Package0HashSha512
        )
        sig_path = store_signature(
            self.archiveted_file_rec.PackageStoragePath, signature
        )
        logger.info(
            "[archivation] signature stored in directory witch package0"
        )
        self.archiveted_file_rec.SignatureHashSha512 = hash_file(
            sha512, sig_path
        )
        logger.info("[archivation] getting signing certificate")
        cert = get_certificate(
            self.archivation_config["signing_info"]["certificate_path"]
        )
        self.archiveted_file_rec.SigningCert = cert.public_bytes(Encoding.PEM)
        logger.info("[archivation] certificate stored in database record")

    def _make_ts1(self):
        logger.info("[archivation] getting timestamp for package0")
        ts1 = self._timestamp_data(
            self.archiveted_file_rec.SignatureHashSha512, "timestamp1"
        )
        self.file_pack_record.IssuingDate = rfc3161ng.get_timestamp(ts1)
        self.archiveted_file_rec.ExpirationDateTS = self._get_expiration_date(
            ts1
        )
        logger.info("[archivation] timestamp recieved succesfully")

    def _store_used_cert_files(self):
        logger.info(
            "[archivation] storing used certificate files and available crls"
            " to archive directory"
        )
        dir_path = create_new_dir_in_location(
            self.archiveted_file_rec.PackageStoragePath, "certificate_files"
        )
        path_ca = self.archivation_config["signing_info"]["certificate_path"]
        path_crl = self.archivation_config["signing_info"]["crl_path"]
        path_tsa_cert = self.archivation_config["TSA_info"]["tsa_cert_path"]
        path_tsa_ca_pem = self.archivation_config["TSA_info"]["tsa_ca_pem"]

        copy_file_to_dir(path_ca, dir_path, "signing_cert.pem")
        copy_file_to_dir(
            path_crl, dir_path, "signing_cert_crl.crl"
        )  # NOTE: comment if you dont want to use CRL
        copy_file_to_dir(path_tsa_cert, dir_path, "tsa_cert.crt")
        copy_file_to_dir(path_tsa_ca_pem, dir_path, "tsa_ca.pem")
        store_ts_data(self.crl, dir_path, "tsa_cert_crl.crl")
        logger.info("[archivation] storage certificate files completed")

    def _make_final_package(self):
        logger.info(
            "[archivation] creating final tar package with archive file"
        )
        final_tar_path = self._make_tar_package_from_dir_content(
            self.archiveted_file_rec.PackageStoragePath, "Package1.tar"
        )
        self.file_pack_record.PackageHashSha512 = hash_file(
            sha512, final_tar_path
        )
        logger.info(
            "[archivation] final package created, archivation successfull"
        )

    def _insert_db_record(self):
        logger.info(
            "[archivation] writing records with gathered data to database"
        )
        try:
            self.db_lib.add_full_records(
                archf_data=self.archiveted_file_rec,
                filep_data=self.file_pack_record,
            )
        except Exception as e:
            logger.warning("unable to write database record of archivation")
            logger.debug("deleting created archived file")
            delete_file(self.archiveted_file_rec.PackageStoragePath)
            raise e

    def _timestamp_data(self, fhash, ts_name):
        logger.debug("getting timestamp for file hash %s", str(fhash))
        ts = get_timestamp(self.archivation_config["TSA_info"], fhash)
        logger.debug(
            "[archivation] timestamp recieved successfully, storing timestamp"
            " to archive direcotry"
        )
        store_ts_data(ts, self.archiveted_file_rec.PackageStoragePath, ts_name)
        logger.debug("[archivation] ts stored")
        return ts

    def _get_file(self, file_path):
        logger.debug(
            "[archivation] getting hash of file on path %s", str(file_path)
        )
        origin_hash = hash_file(sha512, file_path)
        copy_dir_path = create_new_dir_in_location(
            self.storage_dir, str(uuid4())
        )
        logger.debug(
            "[archivation] created archivation directory path: %s",
            str(copy_dir_path),
        )
        self.dst_file_path = copy_file_to_dir(
            file_path, copy_dir_path, self.archiveted_file_rec.FileName
        )
        logger.debug(
            "[archivation] file copied, path: %s", str(self.dst_file_path)
        )
        return copy_dir_path, origin_hash

    def _get_remote_file(self, file_path):
        logger.debug("[archivation] trying to connect to remote storage")
        error_count = 0
        try:
            with closing(
                get_sftp_connection(self.archivation_config["remote_access"])
            ) as sftp_connection:
                logger.debug("[archivation] sftp connection created")
                origin_hash = get_remote_hash(
                    sftp_connection, file_path, sha512
                )
                copy_dir_path = create_new_dir_in_location(
                    self.storage_dir, str(uuid4())
                )
                logger.debug(
                    "[archivation] created archivation directory path: %s",
                    str(copy_dir_path),
                )

                self.dst_file_path = self._copy_remote_file_to_archive(
                    sftp_connection, file_path, copy_dir_path
                )
                logger.debug(
                    "[archivation] remote file copied to destination"
                    " archive: %s",
                    str(self.dst_file_path),
                )
        except Exception as e:
            error_count += 1
            if error_count < 5:
                logger.warning(
                    "Exception occured during SFTP transfer, retrying session",
                    exc_info=True,
                )
            else:
                logger.exception(
                    "Failed to gather remote file",
                    exc_info=True,
                    stack_info=True,
                )
                raise e
        return copy_dir_path, origin_hash

    def _get_expiration_date(self, ts):
        years = self.archivation_config["validity_length"]
        time = rfc3161ng.get_timestamp(ts)
        logger.debug(
            "[archivation] expiration length of timestamp was set to %s",
            str(years),
        )
        return time.replace(year=time.year + years)

    def _get_file_name(self, origin_file_path):
        head, tail = ntpath.split(origin_file_path)
        logger.debug(
            "[archivation] getting file name from path, splited path head: %s,"
            " tail(should be name) %s ",
            str(head),
            str(tail),
        )
        return tail or ntpath.basename(head)

    def _make_tar_package_from_dir_content(self, dir_path, package_name):
        tar_file_path = os.path.join(dir_path, package_name)
        logger.debug(
            "[archivation] creating tar package on path: %s",
            str(tar_file_path),
        )
        create_tar_file_from_dir(dir_path, tar_file_path)
        return tar_file_path

    def __make_signature(self, hash):
        logger.debug("[archivation] getting private key")
        pk = get_private_key(
            self.archivation_config["signing_info"]["private_key_path"],
            self.archivation_config["signing_info"]["pk_password"],
        )
        logger.debug("[archivation] signing data")
        return sign_data(hash, pk)

    def _copy_remote_file_to_archive(
        self, connection_sftp, file_path_to_copy, dst_dir
    ):
        dst = os.path.join(dst_dir, self.archiveted_file_rec.FileName)
        logger.debug("[archivation] copying file from sftp storage")
        connection_sftp.get(remotepath=file_path_to_copy, localpath=dst)
        logger.debug("[archivation] copying finished")
        return dst

    def _validate_data_transfer(self, hash_origin, dst_file_path):
        hash_copy = hash_file(sha512, dst_file_path)
        logger.debug(
            "[archivation] hash of origin file: %s \n hash of copy: %s",
            str(hash_origin),
            str(hash_copy),
        )
        if hash_origin != hash_copy:
            logger.warning(
                "[archivation] hashes of files do not match, file transfer"
                " wasnt succesfull"
            )
            raise FileTransferWasntSuccesfullError(
                "[archivation] hashes of files do not match, file transfer"
                " wasnt succesfull"
            )
        logger.debug("[archivation] digests matched, files are the same")
