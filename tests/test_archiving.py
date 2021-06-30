from archivationsystem.archivation.archiver import Archiver
from archivationsystem.common.yaml_parser import parse_yaml_config
from archivationsystem.database.db_library import (
    DatabaseHandler,
    MysqlConnection,
)


def main():
    config = parse_yaml_config(
        r"/home/nextcloudadmin/ArchivationSystem/config/start_archivation_worker_config.yaml"
    )
    config_for_archiver = config.get("archivation_system_info")
    db_config = config.get("db_config")
    with MysqlConnection(db_config) as db_connection:
        db_lib = DatabaseHandler(db_connection)
        archiver = Archiver(db_lib, config_for_archiver)
        result = archiver.archive("/home/nextcloudadmin/samples/markdown.md", "muzikant2")
        print(result)


if __name__ == "__main__":
    main()
