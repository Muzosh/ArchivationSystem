from common.yaml_parser import parse_yaml_config
from archivation import archiver
from hashlib import sha512

def main():
    
   crt = archiver.get_certificate('/home/server/Desktop/cert.pem')
   print(type(crt))
   prkey = archiver.get_private_key('/home/server/Desktop/key.pem', 'Password1')

   signature = archiver.sign_data(b'ahoj', prkey)

   val = archiver.validate_signature(b'ahoj', signature, crt.public_key())

   print(val)

if __name__ == '__main__':
    main()

