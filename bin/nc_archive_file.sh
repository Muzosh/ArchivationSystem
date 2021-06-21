#!/bin/bash
# BEFORE RUNNING FILL IN THESE VARIABLES (absolute path is recommended)

# SELECT THE CORRECT PYTHON INTERPRETER (where archivationsystem and other required packages are installed)
PYTHON_INTERPRETER=/home/nextcloudadmin/ArchivationSystem/pyvenv/bin/python3.9

# SELECT make_archivation_task.py FILE LOCATION
SCRIPT_LOCATION=/home/nextcloudadmin/ArchivationSystem/bin/make_archivation_task.py

# SELECT make_archivation_task_config.yaml LOCATION
CONFIG_LOCATION=/home/nextcloudadmin/ArchivationSystem/config/make_archivation_task_config.yaml

$PYTHON_INTERPRETER $SCRIPT_LOCATION -c "$CONFIG_LOCATION" -fp $1 -o $2