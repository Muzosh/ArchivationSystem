
# Archivation-System

  

### This repository host my bachelor degree program for Achivation files


## Dependencies

* you must have installed python3 and PyPI
* install all dependencies 
	 > pip3 install -r requirments.txt
* download, install and setup RabbitMQ
	* run rabbitmq server
	* setup control exchange
	* setup exchange and queue for logs (default: exchange - log, queue - logs)
	* you will have to setup queues for every worker
* you must create mysql database
    * you can use scripts inside ./database/sql_scripts

  

## How to execute

* all scripts for creating tasks and executing workers are in root of the project
* all scripts needs their config files
* there is usage print when you run script with correct parameters


* if you are planning to run archivation and validation worker remotly from file storage:
    * setup sftp connection - create keys etc...
    * setup login only using keys
    * setup proper data to configs
    * ensure that user which is used for remote login has access rigths to given directories

### Config formats
* examples can be found in folder ./example_configs&files
* Inside all config examples are comments explaining different fields
* Inside testing_config.yaml are comments for the most common config parameters
* All configs needs part for rabbitmq connection
* General config example for tasks is test_config.yaml
* All workers have defined their own configs
* db_config part can be formated by this -> https://dev.mysql.com/doc/connector-python/en/connector-python-connectargs.html

### Task Scripts

| name | purpose |
|------- | -----| 
| archivation_task.py| Manual creation of task for archivation of given file
| retimestamping_task.py| Regular checking of timestamps expiration dates in database and creating a task for those which validity is ending within 24 ours 
| validation_task.py| Interactive interface for creating tasks for validation of archivated files



### Workers

| name | purpose |
|------- | -----| 
| archivation_worker.py | responsible for consuming archivation tasks from rabbitmq 
| retimestamping_worker.py| responsible for consuming tasks for retimestamping
| validation_worker.py| responsible for validation of archivated files 

