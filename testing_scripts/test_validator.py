from  validation.validator import Validator
from common.yaml_parser import parse_yaml_config

from database.db_library import Mysql_connection, Database_Library
def main():
    config = parse_yaml_config(r'/home/server/Desktop/Archivation-System/example_configs&files/validation_worker_config.yaml')
    db_config = config.get("db_config")
    with Mysql_connection(db_config) as db_connection:
        db_lib = Database_Library(db_connection)
        valdator = Validator(db_lib, config['validation_info'])
        result = valdator.validate(1, ['erik.ch123@gmail.com'])
    print(result)

if __name__ == '__main__':
    main()
