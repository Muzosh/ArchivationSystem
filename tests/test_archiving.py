from archivingsystem.archiving.archiver import Archiver
from archivingsystem.common.yaml_parser import parse_yaml_config
from archivingsystem.database.db_library import (
    DatabaseHandler,
    MysqlConnection,
)


def main():
    config = parse_yaml_config(
        r"/home/nextcloudadmin/archiving-system-nextcloud/config/start_archiving_worker_config.yaml"
    )
    config_for_archiver = config.get("archiving_system_info")
    db_config = config.get("db_config")
    with MysqlConnection(db_config) as db_connection:
        db_lib = DatabaseHandler(db_connection)
        archiver = Archiver(db_lib, config_for_archiver)
        result = archiver.archive("/home/nextcloudadmin/archiving-system-nextcloud/data/samples/markdown.md", "muzikant2")
        print(result)


if __name__ == "__main__":
    main()
