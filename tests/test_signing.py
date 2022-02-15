from archivationsystem.common import utils as common_utils


def main():

    crt = common_utils.get_certificate("/home/nextcloudadmin/certs/myCert.crt")
    prkey = common_utils.get_private_key(
       "/home/nextcloudadmin/certs/myCert.key", "ncadmin"
    )

    signature = common_utils.sign_data(b"test", prkey)

    val = common_utils.validate_signature(b"test", signature, crt.public_key())

    assert val
    
    print("test successful")


if __name__ == "__main__":
    main()
