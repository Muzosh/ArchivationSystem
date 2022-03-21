#!/bin/bash
# BEFORE RUNNING FILL IN THESE VARIABLES (absolute path is recommended)

# SELECT THE CORRECT PYTHON INTERPRETER (where archivingsystem and other required packages are installed)
PYTHON_INTERPRETER=/home/nextcloudadmin/ArchivingSystem/venv/bin/python3.10.2

# SELECT make_archiving_task.py FILE LOCATION
SCRIPT_LOCATION=/home/nextcloudadmin/ArchivingSystem/bin/make_archiving_task.py

# SELECT make_archiving_task_config.yaml FILE LOCATION
CONFIG_LOCATION=/home/nextcloudadmin/ArchivingSystem/config/make_archiving_task_config.yaml

$PYTHON_INTERPRETER $SCRIPT_LOCATION -c "$CONFIG_LOCATION" -fp $1 -o $2