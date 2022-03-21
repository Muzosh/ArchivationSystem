from archivingsystem.common.yaml_parser import parse_yaml_config
from archivingsystem.retimestamping.retimestamping_checker import (
    run_checker_controller
)


def main():
    config = parse_yaml_config(
        r"/home/nextcloudadmin/ArchivingSystem/config/start_retimestamping_scheduler_config.yaml"
    )
    run_checker_controller(config)


if __name__ == "__main__":
    main()
