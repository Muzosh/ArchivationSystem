from archivationsystem.common.yaml_parser import parse_yaml_config
from archivationsystem.retimestamping.retimestamping_checker import (
    run_checker_controller
)


def main():
    config = parse_yaml_config(
        r"/home/nextcloudadmin/ArchivationSystem/config/start_retimestamping_scheduler_config.yaml"
    )
    run_checker_controller(config)


if __name__ == "__main__":
    main()
