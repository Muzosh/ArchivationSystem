
from common.yaml_parser import parse_yaml_config
from archivation import archiver
from pathlib import Path, PurePath
from contextlib import closing
import sys

def raise_system_exit():
    raise SystemExit(
        f"Usage: {sys.argv[0]} (-c | --config) <path to yaml config for Rabbitmq connection>"
        )

    
def parse_arguments(args):
    if not (len(args) == 2):
        raise_system_exit()
    config_path = None
    if args[0] == '-c' or args[0] == '--config':
        config_path = Path(args[1])
    else: 
        raise_system_exit()    
    if not isinstance(config_path, PurePath):
        raise_system_exit() 
    return config_path


def main():
    """
    
    """
    config_path = parse_arguments(sys.argv[1:])
    parsed_config = parse_yaml_config(config_path)

    with closing(
        archiver.get_sftp_connection(
            archiver.parse_config['archivation_system_info']['remote_access']
            )
    ) as sftp_connection:
        hash_f = archiver.get_remote_hash(sftp_connection, '/home/server/Desktop/Untitled 1.odt')
        sftp_connection.get(
            remotepath='/home/server/Desktop/Untitled 1.odt',
            localpath='/home/erik/Desktop/Untitled 1.odt'
        )
        

if __name__ == '__main__':
    main()

