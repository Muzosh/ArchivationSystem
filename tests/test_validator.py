from archivationsystem.common.yaml_parser import parse_yaml_config
from archivationsystem.database.db_library import (
    DatabaseHandler,
    MysqlConnection,
)
from archivationsystem.validation.validator import Validator


def main():
    config = parse_yaml_config(
        r"/home/nextcloudadmin/ArchivationSystem/config/start_validation_worker_config.yaml"
    )
    db_config = config.get("db_config")
    with MysqlConnection(db_config) as db_connection:
        db_lib = DatabaseHandler(db_connection)
        valdator = Validator(db_lib, config["validation_info"])
        result = valdator.validate("20", ["muzosak@seznam.cz"])
    print(result)


if __name__ == "__main__":
    main()
