from hashlib import sha512

from archivationsystem.common import utils
from archivationsystem.common.yaml_parser import parse_yaml_config


def main():
    parsed_config = parse_yaml_config(
        "/home/nextcloudadmin/ArchivationSystem/config/start_retimestamping_worker_config.yaml"
    )

    crl = utils.get_current_crl(
        parsed_config["retimestamping_info"]["TSA_info"]["tsa_crl_url"]
    )

    validation = utils.validate_certificate(
        crl, parsed_config["retimestamping_info"]["TSA_info"]["tsa_ca_pem"]
    )
    assert validation is None

    hash_to_ts = sha512()
    hash_to_ts.update(b"Ahoj")

    ts = utils.get_timestamp(
        parsed_config["retimestamping_info"]["TSA_info"],
        hash_to_ts.digest(),
    )

    ver = utils.verify_timestamp(
        ts,
        hash_to_ts.digest(),
        parsed_config["retimestamping_info"]["TSA_info"],
    )

    assert ver

    crl = utils.get_current_crl(
        parsed_config["retimestamping_info"]["TSA_info"]["tsa_crl_url"]
    )

    validation = utils.validate_certificate(
        crl, parsed_config["retimestamping_info"]["TSA_info"]["tsa_ca_pem"]
    )
    assert validation is None
    print("test successfull")


if __name__ == "__main__":
    main()
