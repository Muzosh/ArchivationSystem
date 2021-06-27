from archivationsystem.common.yaml_parser import parse_yaml_config
from archivationsystem.database.db_library import (
    DatabaseHandler,
    MysqlConnection,
)
from archivationsystem.retimestamping.retimestamper import Retimestamper


def main():
    config = parse_yaml_config(
        r"/home/nextcloudadmin/ArchivationSystem/config/start_retimestamping_worker_config.yaml"
    )
    db_config = config.get("db_config")
    with MysqlConnection(db_config) as db_connection:
        db_lib = DatabaseHandler(db_connection)
        retimestamper = Retimestamper(db_lib, config["retimestamping_info"])
        result = retimestamper.retimestamp(file_id=20)
    
    assert result == "OK"


if __name__ == "__main__":
    main()
