from common.yaml_parser import parse_yaml_config
from database.db_library import DatabaseLibrary, MysqlConnection
from retimestamping.retimestamper import Retimestamper


def main():
    config = parse_yaml_config(
        r"/home/server/Desktop/Archivation-System/example_configs&files/retimestamping_worker_cfg.yaml"
    )
    db_config = config.get("db_config")
    with MysqlConnection(db_config) as db_connection:
        db_lib = DatabaseLibrary(db_connection)
        retimestamper = Retimestamper(db_lib, config["retimestamping_info"])
        result = retimestamper.retimestamp(1)
    print(result)


if __name__ == "__main__":
    main()
