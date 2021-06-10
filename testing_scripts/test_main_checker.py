from common.yaml_parser import parse_yaml_config
from task_makers.retimestamping.retimestamping_checker import (
    checker_controller
)


def main():
    config = parse_yaml_config(
        r"/home/server/Desktop/Archivation-System/example_config/testing_config.yaml"
    )
    checker_controller(config)


if __name__ == "__main__":
    main()
