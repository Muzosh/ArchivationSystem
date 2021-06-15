#!/bin/bash
# BEFORE RUNNING FILL IN 4 VARIABLES (absolute path is recommended)

# SELECT THE CORRECT PYTHON INTERPRETER (where archivationsystem and other required packages are installed)
PYTHON_INTERPRETER=/Users/petr/AppData/Repos/ArchivationSystem/pyArchSys/bin/python3.9

# SELECT make_archivation_task.py FILE LOCATION
SCRIPT_LOCATION=/Users/petr/AppData/Repos/ArchivationSystem/bin/make_archivation_task.py

# SELECT make_archivation_task_config.yaml LOCATION
CONFIG_LOCATION=/Users/petr/AppData/Repos/ArchivationSystem/config/make_archivation_task_config.yaml

$PYTHON_INTERPRETER $SCRIPT_LOCATION -c "$CONFIG_LOCATION" -fp $1 -o $2