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

from common.exceptions import (
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
from common.utils import (
    get_certificate,
    get_remote_hash,
    get_sftp_connection,
    hash_file,
    load_data,
    validate_certificate,
    validate_signature,
    verify_timestamp,
)
from cryptography.exceptions import InvalidSignature

logger = logging.getLogger("Archivation System")


class Validator:
    """
    Validator class is providing functionality
    for archiving proces of file

    validate function should be called

    on init it needs database library object and
    configuration file. Example could be found
    in example_config and it needs validation_info part
    """

    def __init__(self, db_lib, config: dict):
        self.db_lib = db_lib
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
                    "[validation] temporary directory for verification created"
                    " at path %s",
                    str(temp_dir),
                )
                result = self._validate_packages(
                    tar_path, temp_dir, file_packages, archived_file_rec
                )
        except OriginalFileNotValidError:
            result = (
                "archived file with id: {} isnt valid in remote location,   "
                "              archived file is still valid".format(
                    str(archived_file_rec.FileID)
                )
            )
            logger.warning(result)

        except ArchivedFileNotValidCustomException:
            result = (
                "archived file with id: {}                 isnt valid in"
                " archive location".format(str(archived_file_rec.FileID))
            )
            logger.warning(result)

        self._send_results(result, recipients, archived_file_rec.FileName)
        return "OK"

    def _get_archive_record(self, file_info):
        logger.info("[validation] getting archived file record from db")
        logger.debug(
            "[validation] archived file info from task %s", str(file_info)
        )
        if file_info.isdigit():
            return self.db_lib.get_specific_ArchivedFile_record_by_FileId(
                int(file_info)
            )
        elif isinstance(file_info, tuple):
            return self.db_lib.get_fileID_ArchivedFile_rec(
                file_info[1], file_info[0]
            )
        logger.warning("[validation] Wrong task format for validation")
        raise WrongTaskCustomException("Wrong task format for validation")

    def _get_all_sorted_filepackage_records(self, file_id):
        logger.info(
            "[validation] getting all file package records associated with"
            " archived file"
        )
        file_recs = self.db_lib.get_FilePackages_records(file_id)
        file_recs.sort(key=lambda x: x.IssuingDate, reverse=True)
        return file_recs

    def _validate_packages(
        self, tar_path, temp_dir, file_packages, archived_file_rec
    ):
        num = 0
        validation_complete = False
        logger.info("[validation] validating archived file")
        while validation_complete is not True:
            logger.info(
                "[validation] validateing package from path: %s", str(tar_path)
            )
            if "Package1.tar" in tar_path:
                try:
                    result = self._validate_initial_pacakge(
                        tar_path,
                        temp_dir,
                        file_packages[num],
                        archived_file_rec,
                    )
                    validation_complete = True
                    logger.info(
                        "[validation] validation of initial package complete"
                    )
                except (
                    TimestampInvalidCustomException,
                    DigestsNotMatchedCustomException,
                    InvalidSignature,
                    FileNotInDirectoryCustomException,
                    CertificateNotValidCustomException,
                ):
                    logger.warning("[validation] package invalid")
                    raise ArchivedFileNotValidCustomException(
                        "[validation] package invalid"
                    )
            elif "PackageF" in tar_path:
                try:
                    tar_path = self._validate_package(
                        tar_path, temp_dir, file_packages[num]
                    )
                    logger.info(
                        "[validation] validation of onion package complete"
                    )
                except (
                    TimestampInvalidCustomException,
                    DigestsNotMatchedCustomException,
                    FileNotInDirectoryCustomException,
                    CertificateNotValidCustomException,
                ):
                    logger.warning("[validation] package invalid")
                    raise ArchivedFileNotValidCustomException(
                        "[validation] package invalid"
                    )

            else:
                logger.exception(
                    "[validation] Path to package for validation isnt correct",
                    str(tar_path),
                )
                raise WrongPathToArchivedFileCustomException(
                    "Wrong file for validation"
                )
            num += 1
        return result

    def _validate_package(self, tar_path, temp_dir, file_package):
        logger.debug(
            "[validation] validating package %s hashes with db", str(tar_path)
        )
        self._verify_package_hashes(
            file_package.PackageHashSha512, hash_file(sha512, tar_path)
        )
        pack_path = self._extract_tar_to_temp_dir(
            tar_path, "PackageF", temp_dir
        )
        logger.debug("[validation] verifying timestamp and certificate")
        self._verify_package_timestamp(pack_path)
        self._verify_certificate_with_crl(
            pack_path, "tsa_cert_crl.crl", "tsa_ca.pem"
        )
        return self._get_file_path_from_dir(pack_path, "Package")

    def _validate_initial_pacakge(
        self, package_path, temp_dir, file_package, archived_file_rec
    ):
        logger.debug("[validation] getting package1 hash and verifing it")
        hash_package1 = hash_file(sha512, package_path)
        self._verify_package_hashes(
            file_package.PackageHashSha512, hash_package1
        )
        logger.debug("[validation] extracting package1")
        extract_path = self._extract_tar_to_temp_dir(
            package_path, "Package1", temp_dir
        )

        logger.debug("[validation] getting package0 hash and verifing it")
        package0_path = self._get_file_path_from_dir(extract_path, "Package0")
        hash_package0 = hash_file(sha512, package0_path)
        self._verify_package_hashes(
            archived_file_rec.Package0HashSha512, hash_package0
        )

        logger.debug("[validation] verifying signature and its timestamp")
        hash_signature = self._verify_signature(
            extract_path,
            hash_package0,
            archived_file_rec.SignatureHashSha512,
        )
        self._verify_timestamp(extract_path, "timestamp1", hash_signature)

        logger.debug("[validation] extracting package0")
        extrack_pack0_path = self._extract_tar_to_temp_dir(
            package0_path, "Package0", temp_dir
        )

        logger.debug(
            "[validation] verifying archived file package hash with hash"
            " from database"
        )
        hash_archived_file = hash_file(
            sha512,
            os.path.join(extrack_pack0_path, archived_file_rec.FileName),
        )
        self._verify_package_hashes(
            archived_file_rec.OriginFileHashSha512, hash_archived_file
        )

        self._verify_timestamp(
            extrack_pack0_path, "timestamp0", hash_archived_file
        )

        logger.debug("[validation] verifying certificates")
        self._verify_certificate_with_crl(
            extract_path, "tsa_cert_crl.crl", "tsa_ca.pem"
        )
        self._verify_certificate_with_crl(
            extract_path, "signing_cert_crl.crl", "signing_cert.pem"
        )  # NOTE: comment if you dont want to use CRL

        logger.debug(
            "[validation] verifying archived file from archive storage with"
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
        text_massage = MIMEText(text, "plain")
        msg.attach(text_massage)
        context = ssl._create_unverified_context()
        with smtplib.SMTP_SSL(
            self.config["contact"]["email_server"], 465, context=context
        ) as smtp_serv:
            smtp_serv.login(
                sender_mail, self.config["contact"]["sender_password"]
            )
            smtp_serv.sendmail(sender_mail, recipients, msg.as_string())

    def _extract_tar_to_temp_dir(self, tar_path, tar_name, temp_dir_path):
        tar_name = self.__get_file_name(tar_path)
        extract_path = os.path.join(temp_dir_path, tar_name)
        logger.debug(
            "[validation] extracting tar package from path: %s to temp"
            " dir: %s",
            tar_path,
            extract_path,
        )
        with tarfile.open(tar_path, "r:") as tarf:
            tarf.extractall(path=extract_path)
        return extract_path

    def _verify_package_hashes(self, hash_db, hash_pack):
        logger.debug(
            "[validation] hash from db: %s \n hash of origin file: %s",
            str(hash_db),
            str(hash_pack),
        )
        if hash_db != base64.b64encode(hash_pack):
            logger.warning(
                "[validation] hashes of files do not match, validation wasnt"
                " succesffull"
            )
            raise DigestsNotMatchedCustomException(
                "[validation] hashes of files do not match, validation wasnt"
                " succesffull"
            )
        logger.info("[validation] digests metched, files are the same")

    def _verify_package_timestamp(self, pack_path):
        data_path = self._get_file_path_from_dir(pack_path, "Package")
        logger.debug(
            "[validation] getting hash of package to verify from path %s",
            str(data_path),
        )
        data = hash_file(sha512, data_path)
        logger.debug("[validation] verifying package timestamp")
        self._verify_timestamp(pack_path, "timestamp", data)

    def _verify_signature(self, extract_path, signed_data, signature_hash_db):
        signature_path = os.path.join(extract_path, "signature.sig")
        logger.debug(
            "[validation] getting hash of signature from path %s",
            str(signature_path),
        )
        hash_signature = hash_file(sha512, signature_path)
        self._verify_package_hashes(signature_hash_db, hash_signature)

        signature = load_data(signature_path)
        certs_folder_path = os.path.join(extract_path, "certificate_files")
        cert_path = self._get_file_path_from_dir(
            certs_folder_path, "signing_cert.pem"
        )
        logger.debug(
            "[validation] loading certificate from path %s", str(cert_path)
        )
        cert = get_certificate(cert_path)
        validate_signature(signed_data, signature, cert.public_key())
        logger.debug("[validation] verification of signature was succesful")
        return hash_signature

    def _verify_timestamp(self, dir_path, file_name, data):
        logger.debug("[validation] verification of timestamp")
        ts_path = self._get_file_path_from_dir(dir_path, file_name)
        logger.debug("[validation] loading timestamp")
        ts = load_data(ts_path)
        logger.debug("[validation] verifying timestamp")
        if not (verify_timestamp(ts, data, self.config["TSA_info"])):
            logger.exception(
                "[validation] Timestamp invalid, timestamp path: %s",
                str(ts_path),
            )
            raise TimestampInvalidCustomException("Timestamp invalid")
        logger.debug("[validation] timestamp is valid")

    def _get_file_path_from_dir(self, dir_path, file_name):
        logger.debug(
            "[validation] searching for file: %s in directory: %s",
            str(file_name),
            str(dir_path),
        )
        files = [f for f in os.listdir(dir_path) if file_name in f]
        if not files:
            logger.exception(
                "[validation] no file with given file name: %s was found in"
                " dir: %s",
                str(file_name),
                str(dir_path),
            )
            raise FileNotInDirectoryCustomException(
                "No files with given name in directory. name: %s", file_name
            )
        logger.debug("[validation] file found in directory")
        return os.path.join(dir_path, files[0])

    def _verify_certificate_with_crl(self, dir_path, crl_name, cert_name):
        crl = load_data(os.path.join(dir_path, "certificate_files", crl_name))
        logger.debug("[validation] verifying used certificate with crl")
        validate_certificate(
            crl, os.path.join(dir_path, "certificate_files", cert_name)
        )
        logger.debug("[validation] verification of certificate successfull")

    def _verify_original_file(self, archived_file_hash, origin_path):
        logger.debug("[validation] verifying original file hash with archived")
        if self.config["remote_access"] is False:
            logger.debug("[validation] file should be on local disk")
            hash_origin = hash_file(sha512, origin_path)
        else:
            logger.debug("[validation] file should be on remote location disk")
            hash_origin = self._get_remote_file_hash(origin_path)
        logger.debug(
            "[validation] gathering origin file hash success full,"
            " verification..."
        )
        try:
            self._verify_package_hashes(archived_file_hash, hash_origin)
        except (
            UnableToGetRemoteFileDigestCustomException,
            DigestsNotMatchedCustomException,
        ):  # as e:
            raise OriginalFileNotValidError("Remote file is not the same")

    def _get_remote_file_hash(self, file_path):
        logger.debug(
            "[validation] creating sftp connection for getting origin file"
            " hash if it still same"
        )
        with closing(
            get_sftp_connection(self.config["remote_access"])
        ) as sftp_connection:
            logger.debug(
                "[validation] connection created successfully, getting hash of"
                " remote file"
            )
            try:
                return get_remote_hash(sftp_connection, file_path, sha512)
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
            "[validation] getting file name from path, splited path head: %s,"
            " tail(should be name) %s ",
            str(head),
            str(tail),
        )
        return tail or ntpath.basename(head)
