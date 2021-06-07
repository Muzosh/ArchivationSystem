from pathlib import Path, PurePath
import sys
p = Path(__file__) / Path(r"").absolute()
sys.path.insert(0, str(p))

from common.yaml_parser import parse_yaml_config
from archivation import archiver
from hashlib import sha512

def main():
    parsed_config = parse_yaml_config('/home/server/Desktop/Archivation-System/example_configs&files/archivation_worker_config.yaml')
    
    crl = archiver.get_current_crl(parsed_config['archivation_system_info']['TSA_info']['tsa_crl_url'])

    validation = archiver.validate_certificate(crl, parsed_config['archivation_system_info']['TSA_info']['tsa_ca_pem'])
    print(validation)

    hash_to_ts = sha512()
    hash_to_ts.update(b'Ahoj')
    
    ts = archiver.get_timestamp(parsed_config['archivation_system_info']['TSA_info'],hash_to_ts.digest())

    #print(ts)
    with open('/home/server/Desktop/tsxxx', 'wb') as f:
        f.write(ts)

    with open('/home/server/Desktop/tsxxx', 'rb') as f:
        tss = f.read()

    
    ver = archiver.verify_timestamp(tss, hash_to_ts.digest(), parsed_config['archivation_system_info']['TSA_info'])

    print(ver)

    crl = archiver.get_current_crl(parsed_config['archivation_system_info']['TSA_info']['tsa_crl_url'])

    validation = archiver.validate_certificate(crl, parsed_config['archivation_system_info']['TSA_info']['tsa_ca_pem'])
    print(validation)

if __name__ == '__main__':
    main()

