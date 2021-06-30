import base64
import logging
import ntpath
import os
import smtplib
import ssl
import tarfile
from contextlib import closing
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from hashlib import sha512
from tempfile import TemporaryDirectory

from cryptography.exceptions import InvalidSignature

from ..common import utils as common_utils
from ..common.exceptions import (
    ArchivedFileNotValidCustomException,
    CertificateNotValidCustomException,
    DigestsNotMatchedCustomException,
    FileNotInDirectoryCustomException,
    OriginalFileNotValidError,
    TimestampInvalidCustomException,
    UnableToGetRemoteFileDigestCustomException,
    WrongPathToArchivedFileCustomException,
    WrongTaskCustomException,
)

logger = logging.getLogger("archivation_system_logging")


class Validator:
    """
    Validator class is providing functionality
    for archiving proces of file

    validate function should be called

    on init it needs database library object and
    configuration file. Example could be found
    in example_config and it needs validation_info part
    """

    def __init__(self, db_handler, config: dict):
        self.db_handler = db_handler
        self.config = config

    def validate(self, file_info, recipients):
        """
        This will validate archived package. It needs
        file info which could be file ID or name and owner
        to determine which archived file will be validated.
        It needs list of recipients email which will be informed
        about validation result
        """
        archived_file_rec = self._get_archive_record(file_info)
        file_packages = self._get_all_sorted_filepackage_records(
            archived_file_rec.FileID
        )
        tar_path = self._get_file_path_from_dir(
            archived_file_rec.PackageStoragePath, "Package"
        )
        try:
            with TemporaryDirectory() as temp_dir:
                logger.debug(
                    "temporary directory for verification created at: %s",
                    str(temp_dir),
                )
                result = self._validate_packages(
                    tar_path, temp_dir, file_packages, archived_file_rec
                )
        except OriginalFileNotValidError:
            result = (
                "archived file with id: {} isnt valid in remote location,"
                " archived file is still valid".format(
                    str(archived_file_rec.FileID)
                )
            )
            logger.warning(result)
        except ArchivedFileNotValidCustomException:
            result = (
                "archived file with id: {} isnt valid in archive location"
                .format(str(archived_file_rec.FileID))
            )
            logger.warning(result)

        self._send_results(result, recipients, archived_file_rec.FileName)
        return "OK"

    def _get_archive_record(self, file_info):
        logger.debug("getting archived file info: %s", str(file_info))
        if file_info.isdigit():
            return (
                self.db_handler.get_specific_archived_file_record_by_file_id(
                    int(file_info)
                )
            )
        elif isinstance(file_info, tuple):
            file_id = self.db_handler.get_file_id_archived_file_rec(
                file_info[1], file_info[0]
            )
            return (
                self.db_handler.get_specific_archived_file_record_by_file_id(
                    file_id
                )
            )
        logger.exception("Wrong task format for validation")
        raise WrongTaskCustomException("Wrong task format for validation")

    def _get_all_sorted_filepackage_records(self, file_id):
        logger.debug(
            "getting all file package records associated with archived file"
            " with id: %s",
            file_id,
        )
        file_recs = self.db_handler.get_file_package_records(file_id)
        file_recs.sort(key=lambda x: x.IssuingDate, reverse=True)
        return file_recs

    def _validate_packages(
        self, tar_path, temp_dir, file_packages, archived_file_rec
    ):
        num = 0
        validation_complete = False
        logger.info("validating archived file")
        while validation_complete is not True:
            logger.debug("validating package from path: %s", str(tar_path))
            if "Package1.tar" in tar_path:
                try:
                    result = self._validate_initial_package(
                        tar_path,
                        temp_dir,
                        file_packages[num],
                        archived_file_rec,
                    )
                    validation_complete = True
                    logger.info("validation of initial package complete")
                except (
                    TimestampInvalidCustomException,
                    DigestsNotMatchedCustomException,
                    InvalidSignature,
                    FileNotInDirectoryCustomException,
                    CertificateNotValidCustomException,
                ):
                    logger.warning("package invalid")
                    raise ArchivedFileNotValidCustomException(
                        "package invalid"
                    )
            elif "PackageF" in tar_path:
                try:
                    tar_path = self._validate_package(
                        tar_path, temp_dir, file_packages[num]
                    )
                    logger.info("validation of onion package complete")
                except (
                    TimestampInvalidCustomException,
                    DigestsNotMatchedCustomException,
                    FileNotInDirectoryCustomException,
                    CertificateNotValidCustomException,
                ):
                    logger.exception("package is invalid: %s", tar_path)
                    raise ArchivedFileNotValidCustomException(
                        "package is invalid: {}".format(tar_path)
                    )
            else:
                logger.exception(
                    "Path to package for validation isnt correct: %s",
                    tar_path,
                )
                raise WrongPathToArchivedFileCustomException(
                    "Path to package for validation isnt correct: {}".format(
                        tar_path
                    )
                )
            num += 1
        return result

    def _validate_package(self, tar_path, temp_dir, file_package):
        logger.debug("validating package %s hashes with db", str(tar_path))
        self._verify_package_hashes(
            file_package.PackageHashSha512,
            common_utils.get_file_hash(sha512, tar_path),
        )
        temp_extracted_package_path = self._extract_tar_to_temp_dir(
            tar_path, temp_dir
        )

        logger.info("verifying timestamp and certificate")
        self._verify_package_timestamp(temp_extracted_package_path)
        self._verify_certificate_with_crl(
            temp_extracted_package_path, "tsa_cert_crl.crl", "tsa_ca_cert.pem"
        )
        return self._get_file_path_from_dir(
            temp_extracted_package_path, "Package"
        )

    def _validate_initial_package(
        self, package_path, temp_dir, file_package, archived_file_rec
    ):
        logger.info("getting package1 hash and verifing it")
        package1_hash = common_utils.get_file_hash(sha512, package_path)
        self._verify_package_hashes(
            file_package.PackageHashSha512, package1_hash
        )

        logger.info("extracting package1")
        extract_path = self._extract_tar_to_temp_dir(package_path, temp_dir)

        logger.info("getting package0 hash and verifing it")
        package0_path = self._get_file_path_from_dir(extract_path, "Package0")
        package0_hash = common_utils.get_file_hash(sha512, package0_path)
        self._verify_package_hashes(
            archived_file_rec.Package0HashSha512, package0_hash
        )

        logger.info("verifying signature and its timestamp")
        hash_signature = self._verify_signature(
            extract_path,
            package0_hash,
            archived_file_rec.SignatureHashSha512,
        )
        self._verify_timestamp(extract_path, "timestamp1", hash_signature)

        logger.info("extracting package0")
        extrack_pack0_path = self._extract_tar_to_temp_dir(
            package0_path, "Package0", temp_dir
        )

        logger.info(
            "verifying archived file package hash with hash from database"
        )
        hash_archived_file = common_utils.get_file_hash(
            sha512,
            os.path.join(extrack_pack0_path, archived_file_rec.FileName),
        )
        self._verify_package_hashes(
            archived_file_rec.OriginFileHashSha512, hash_archived_file
        )

        self._verify_timestamp(
            extrack_pack0_path, "timestamp0", hash_archived_file
        )

        logger.info("verifying certificates")
        self._verify_certificate_with_crl(
            extract_path, "tsa_cert_crl.crl", "tsa_ca_cert.pem"
        )
        # self._verify_certificate_with_crl( - to validate our own CRL
        #     extract_path, "signing_cert_crl.crl", "signing_cert.pem"
        # )

        logger.info(
            "verifying archived file from archive storage with"
            " original storage"
        )

        self._verify_original_file(
            archived_file_rec.OriginFileHashSha512,
            archived_file_rec.OriginalFilePath,
        )
        return True

    def _send_results(self, result, recipients, file_name):
        sender_mail = self.config["contact"]["sender_email"]
        msg = MIMEMultipart()
        msg["Subject"] = "Verification of file validity for: {}".format(
            file_name
        )
        msg["To"] = ", ".join(recipients)
        msg["From"] = sender_mail
        if result is True:
            text = "Result: file {} is still valid".format(file_name)
        else:
            text = """\
            Result: {result}
            Please contact administrator.

            DO NOT RESPOND TO THIS EMAIL! Contact details are below.

            Contact details:
            email: {email}
            phone number: {phone}
            """.format(
                result=result,
                email=self.config["contact"]["email"],
                phone=self.config["contact"]["phone"],
            )
        text_message = MIMEText(text, "plain")
        msg.attach(text_message)
        context = ssl._create_unverified_context()
        with smtplib.SMTP_SSL(
            self.config["contact"]["email_server"], 465, context=context
        ) as smtp_serv:
            smtp_serv.login(
                sender_mail, self.config["contact"]["sender_password"]
            )
            smtp_serv.sendmail(sender_mail, recipients, msg.as_string())

    def _extract_tar_to_temp_dir(self, tar_path, temp_dir_path):
        tar_name = self.__get_file_name(tar_path)
        extract_path = os.path.join(temp_dir_path, tar_name)
        logger.debug(
            "extracting tar package from path: %s to temp dir: %s",
            tar_path,
            extract_path,
        )
        with tarfile.open(tar_path, "r:") as tarf:
            tarf.extractall(path=extract_path)
        return extract_path

    def _verify_package_hashes(self, db_hash, package_hash):
        logger.debug(
            "hash from db: %s \n hash of package file: %s",
            str(db_hash),
            str(package_hash),
        )
        if db_hash != base64.b64encode(package_hash):
            logger.exception(
                "hash from db and hash of package file do not match"
            )
            raise DigestsNotMatchedCustomException(
                "hash from db and hash of package file do not match"
            )
        logger.info("hash from db and hash of package file matched")

    def _verify_package_timestamp(self, pack_path):
        data_path = self._get_file_path_from_dir(pack_path, "Package")
        logger.debug(
            "getting hash of package to verify from path %s",
            str(data_path),
        )
        data = common_utils.get_file_hash(sha512, data_path)
        logger.info("verifying package timestamp")
        self._verify_timestamp(pack_path, "timestamp", data)

    def _verify_signature(self, extract_path, signed_data, signature_hash_db):
        signature_path = os.path.join(extract_path, "signature.sig")
        logger.debug(
            "getting hash of signature from path %s",
            str(signature_path),
        )
        hash_signature = common_utils.get_file_hash(sha512, signature_path)
        self._verify_package_hashes(signature_hash_db, hash_signature)

        signature = common_utils.load_data(signature_path)
        certs_folder_path = os.path.join(extract_path, "certificate_files")
        cert_path = self._get_file_path_from_dir(
            certs_folder_path, "signing_cert.pem"
        )

        logger.debug("loading certificate from path %s", str(cert_path))
        cert = common_utils.get_certificate(cert_path)
        common_utils.validate_signature(
            signed_data, base64.b64decode(signature), cert.public_key()
        )
        return hash_signature

    def _verify_timestamp(self, dir_path, file_name, data):
        logger.info("verification of timestamp")
        ts_path = self._get_file_path_from_dir(dir_path, file_name)
        logger.info("loading timestamp")
        ts = common_utils.load_data(ts_path)
        logger.info("verifying timestamp")
        if not (
            common_utils.verify_timestamp(ts, data, self.config["TSA_info"])
        ):
            logger.exception(
                "Timestamp invalid, timestamp path: %s",
                str(ts_path),
            )
            raise TimestampInvalidCustomException("Timestamp invalid")
        logger.info("timestamp is valid")

    def _get_file_path_from_dir(self, dir_path, file_name):
        logger.debug(
            "searching for file: %s in directory: %s",
            str(file_name),
            str(dir_path),
        )
        files = [f for f in os.listdir(dir_path) if file_name in f]
        if not files:
            logger.exception(
                "no file with given file name: %s was found in dir: %s",
                str(file_name),
                str(dir_path),
            )
            raise FileNotInDirectoryCustomException(
                "No files with given name in directory. name: {}".format(
                    file_name
                )
            )
        return os.path.join(dir_path, files[0])

    def _verify_certificate_with_crl(self, dir_path, crl_name, cert_name):
        crl = common_utils.load_data(
            os.path.join(dir_path, "certificate_files", crl_name)
        )

        logger.info("verifying used certificate with crl")
        common_utils.validate_certificate(
            crl, os.path.join(dir_path, "certificate_files", cert_name)
        )

    def _verify_original_file(self, archived_file_hash, origin_path):
        logger.info("verifying original file hash with archived")
        if self.config["remote_access"] is False:
            logger.info("file should be on local disk")
            hash_origin = common_utils.get_file_hash(sha512, origin_path)
        else:
            logger.info("file should be on remote location disk")
            hash_origin = self._get_remote_file_hash(origin_path)
        logger.info(
            "gathering origin file hash successfull, verification..."
        )
        try:
            self._verify_package_hashes(archived_file_hash, hash_origin)
        except (
            UnableToGetRemoteFileDigestCustomException,
            DigestsNotMatchedCustomException,
        ):  # as e:
            raise OriginalFileNotValidError("Remote file is not the same")

    def _get_remote_file_hash(self, file_path):
        logger.info(
            "creating sftp connection for getting origin file"
            " hash if it still same"
        )
        with closing(
            common_utils.get_sftp_connection(self.config["remote_access"])
        ) as sftp_connection:
            logger.info(
                "connection created successfully, getting hash of remote file"
            )
            try:
                return common_utils.get_remote_hash(
                    sftp_connection, file_path, sha512
                )
            except Exception:  # as e: - was unused
                logger.exception(
                    "Unable to get remote file digest",
                    exc_info=True,
                    stack_info=True,
                )
                raise UnableToGetRemoteFileDigestCustomException(
                    "Unable to get remote file digest"
                )

    def __get_file_name(self, path):
        head, tail = ntpath.split(path)
        logger.debug(
            "getting file name from path, splited path head: %s,"
            " tail(should be name) %s ",
            str(head),
            str(tail),
        )
        return tail or ntpath.basename(head)
