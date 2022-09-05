from archivingsystem.common.yaml_parser import parse_yaml_config
from archivingsystem.database.db_library import (
    DatabaseHandler,
    MysqlConnection,
)
from archivingsystem.validation.validator import Validator


def main():
    config = parse_yaml_config(
        r"/home/nextcloudadmin/archiving-system-nextcloud/config/start_validation_worker_config.yaml"
    )
    db_config = config.get("db_config")
    with MysqlConnection(db_config) as db_connection:
        db_lib = DatabaseHandler(db_connection)
        valdator = Validator(db_lib, config["validation_info"])
        result = valdator.validate("1", ["muzosak@seznam.cz"])
    print(result)


if __name__ == "__main__":
    main()
