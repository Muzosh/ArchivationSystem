from common.yaml_parser import parse_yaml_config
from database.db_library import DatabaseLibrary, MysqlConnection
from validation.validator import Validator


def main():
    config = parse_yaml_config(
        r"/home/server/Desktop/Archivation-System/example_config/validation_worker_config.yaml"
    )
    db_config = config.get("db_config")
    with MysqlConnection(db_config) as db_connection:
        db_lib = DatabaseLibrary(db_connection)
        valdator = Validator(db_lib, config["validation_info"])
        result = valdator.validate(1, ["erik.ch123@gmail.com"])
    print(result)


if __name__ == "__main__":
    main()
