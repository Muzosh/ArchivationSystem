import os
import tarfile
from shutil import copy2, rmtree

import paramiko
import requests
import rfc3161ng
from cryptography import x509

# from cryptography.exceptions import InvalidSignature - was unused
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import asymmetric, hashes, serialization
from OpenSSL import crypto

from .exceptions import CertificateNotValidCustomException


def store_ts_data(data, path, name):
    """
    Function responsible for writing bits of data
    to given path directory and asigning it a
    name from function.
    """
    with open(os.path.join(path, name), "wb") as f:
        f.write(data)


def load_data(path):
    """
    Loads bytes of data from system path
    """
    with open(path, "rb") as f:
        data = f.read()
    return data


def get_timestamp(tsa_info: dict, file_hash):
    """
    Function responsible for getting timstamp
    for bits of data. It is creating connection to
    remote timestamping authority.
    It needs hash data or bytes of small object
    and it needs dictionary with information to
    create connection.
    dictionary example:
    TSA_info: {
        tsa_tsr_url: 'https://freetsa.org/tsr'
        tsa_cert_path: '/home/server/Downloads/tsa.crt'
    }
    Returns bytes with timestamp tsr
    """
    tsa_cert = load_data(tsa_info["tsa_cert_path"])
    remote_tsa = rfc3161ng.RemoteTimestamper(
        url=tsa_info["tsa_tsr_url"], certificate=tsa_cert, hashname="sha512"
    )
    data_ts = remote_tsa(file_hash)
    return data_ts


def verify_timestamp(ts, data, info: dict):
    """
    Function for verifying timestamp respones.
    It will create connection to timestamping authority
    which need dictionary like this
    TSA_info: {
        tsa_tsr_url: 'https://freetsa.org/tsr'
        tsa_cert_path: '/home/server/Downloads/tsa.crt'
    }
    It need data that was timestamped and bytes with ts
    returns true or false if timestamp is corect
    """
    tsa_cert = load_data(info["tsa_cert_path"])
    remote_tsa = rfc3161ng.RemoteTimestamper(
        url=info["tsa_tsr_url"], certificate=tsa_cert, hashname="sha512"
    )
    return remote_tsa.check(ts, data)


def sign_data(data, private_key):
    """
    Function for signig byte data with given private key.
    """
    signature = private_key.sign(
        data,
        asymmetric.padding.PSS(
            mgf=asymmetric.padding.MGF1(hashes.SHA512()),
            salt_length=asymmetric.padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA512(),
    )
    return signature


def get_private_key(path, password):
    """
    Function for loading private key from path
    with password
    returning private key
    """
    with open(path, "rb") as pk:
        private_key = serialization.load_pem_private_key(
            pk.read(), password=password.encode(), backend=default_backend()
        )
    return private_key


def get_certificate(path):
    """
    Function for loading PEM certificate from given
    path.
    It will return x509 object with certificate
    """
    with open(path, "rb") as cert:
        crt = cert.read()
        certificate = x509.load_pem_x509_certificate(crt, default_backend())
    return certificate


def get_public_key(path):
    """
    Function for loading stored public key
    from given path
    """
    with open(path, "rb") as pk:
        k = pk.read()
        public_key = serialization.load_pem_public_key(
            k, backend=default_backend()
        )
    return public_key


def store_signature(path, signature):
    """
    Function to store bytes of signature
    to given directory path at gives it name
    signature.sig
    """
    path = os.path.join(path, "signature.sig")
    with open(path, "wb") as f:
        f.write(signature)
    return path


def validate_signature(data, signature, public_key):
    """
    Function for validating signatature of data.
    It need public key, signature and signed bytes data
    returns true if signature is valid else it will raise exception
    """

    public_key.verify(
        signature,
        data,
        asymmetric.padding.PSS(
            mgf=asymmetric.padding.MGF1(hashes.SHA512()),
            salt_length=asymmetric.padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA512(),
    )
    return True


def create_tar_file_from_dir(dir_path, tar_path):
    """
    This will create tar archive, without any compression,
    from files within directory and deletes original files
    to remove duplicits. It will returns path to created
    tar archive
    """
    with tarfile.open(tar_path, "w:") as tarf:  # uncompressed mode
        for f in os.listdir(dir_path):
            fp = os.path.join(dir_path, f)
            if not fp == tar_path:
                tarf.add(fp, arcname=f)
                delete_file(fp)


def delete_file(path):
    """
    This will delete directory or file from
    given path
    """
    if os.path.isdir(path):
        rmtree(path)
    if os.path.isfile(path):
        os.remove(path)


def get_file_hash(hash, file_path):
    """
    Function for hashing file on given path.
    It needs to get specify hash function which
    will be applied (example haslib.sha512)
    It will hash even big files without killing
    ram memmory since it uses buffering.
    Returning bytes with digest
    """
    file_hash = hash()
    with open(file_path, "rb") as f:
        buffer = f.read(8192)
        while buffer != b"":
            file_hash.update(buffer)
            buffer = f.read(8192)
    return file_hash.digest()


def get_remote_hash(connection_sftp, path, hash):
    """
    Function for getting file hash from remote sftp
    storage withou moving file.
    It needs sftp connection from paramiko.SFTPClient
    Path to file on remote storage and hash function
    wich will be applied (hashlib.sha512)
    """
    with connection_sftp.open(path, "rb") as f:
        file_hash = hash()
        buffer = f.read(8192)
        while buffer != b"":
            file_hash.update(buffer)
            buffer = f.read(8192)
    return file_hash.digest()


def get_sftp_connection(config: dict):
    """
    Function for creating sftp connection to remote
    storage. It will return sftp_conneciton from
    paramico.SFTPClient
    It needs dictionary with config.
    Exmple of config format:
    {
        host: ''
        port: ''
        credentials:
            username: ''
            password: '' password to key
            key_filepath: ''
    }
    """

    transport = paramiko.Transport((config["host"], config["port"]))
    username = config["credentials"]["username"]
    password = config["credentials"]["password"]
    key_filepath = config["credentials"]["key_filepath"]

    key = paramiko.RSAKey.from_private_key_file(
        filename=key_filepath, password=password
    )

    transport.connect(username=username, pkey=key)

    return paramiko.SFTPClient.from_transport(transport)


def validate_certificate(crl_content, ca_file_path):
    """
    Function for validating if certificate was correct
    at given time. It is validating it with its crl content
    It need crl bytes and path to certificate
    return true if valid
    """
    crl = crypto.load_crl(crypto.FILETYPE_PEM, crl_content)

    crl_crypto = crl.to_cryptography()

    with open(ca_file_path, "rb") as f:
        ca_cert = f.read()

    ca = crypto.load_certificate(crypto.FILETYPE_PEM, ca_cert)

    valid = crl_crypto.is_signature_valid(
        ca.get_pubkey().to_cryptography_key()
    )
    revoked = crl_crypto.get_revoked_certificate_by_serial_number(
        ca.get_serial_number()
    )
    if revoked:
        raise CertificateNotValidCustomException("certificate was revoked")
    if not (valid):
        raise CertificateNotValidCustomException(
            "certificate or crl is invalid"
        )


def get_current_crl(tsa_crl_url):
    """
    Function for downloading crl from tsa_crl_url and returning
    content.
    """
    res = requests.get(tsa_crl_url)
    return res.content


def copy_file_to_dir(file_path_to_copy, dst_dir, name):
    """
    Function for copying file to other directory
    It needs path to file which has to be copied
    and destination directory and name under which
    it will be stored
    """
    dst = os.path.join(dst_dir, name)
    copy2(src=file_path_to_copy, dst=dst)
    return dst


def create_new_dir_in_location(new_dir_path, name):
    """
    Function for creating new directory in given
    directory location with given name
    Parrent directory must exist
    Return path to new directory
    """
    path = os.path.join(new_dir_path, name)
    os.mkdir(path)
    return path
