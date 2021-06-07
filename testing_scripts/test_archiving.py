from archivation.archiver import Archiver
from common.yaml_parser import parse_yaml_config

from database.db_library import Mysql_connection, Database_Library
def main():
    config = parse_yaml_config(r'/home/server/Desktop/Archivation-System/example_configs&files/archivation_worker_config.yaml')
    config_for_archiver = config.get("archivation_system_info")
    db_config = config.get("db_config")
    with Mysql_connection(db_config) as db_connection:
            db_lib = Database_Library(db_connection)
            archiver = Archiver(db_lib, config_for_archiver)
            result = archiver.archive('/home/server/kite-installer', 'User1')
            print(result)
if __name__ == '__main__':
    main()

