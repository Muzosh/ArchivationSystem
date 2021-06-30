[comment]: #
# Archivation system for Nextcloud

## Installation and setup
1. install python3 and PyPI (pip)
1. (optional) create virtual environment and activate it
1. install archivationsystem with dependencies:
    > pip install \<path-to-this-project\>
1. (optional) install linter, formatter, etc. used for this project
    > pip install flake8 black rope bandit
1. download, install and setup RabbitMQ
    * install via *./docs/rabbimq_setup.sh* installation script
    * run commands:
    ```
    sudo rabbitmq−plugins enable rabbitmq_management

    sudo rabbitmqctl add_user „ncadmin“ (password „ncadmin“)

    sudo rabbitmqctl add_vhost archivationsystem

    sudo rabbitmqctl set_permissions -p „archivationsystem“ „ncadmin“ „.*“ „.*“ „.*“

    sudo rabbitmqctl set_user_tags ncadmin administrator
    ```
    * create queues: `archivation`, `failed_tasks`, `validation`, `retimestamping`, `archivation_system_logging` 
	* create new exchange:
        * `name = log`
        * `type = topic`
        * `bind = archivation_system_logging`
        * `routing_key = archivation_system_logging.*`
1. create mysql tables
    * scripts are available in ./data/sqlscripts
1. in Nextcloud app store install "Workflow external scripts" and **replace** *\<location-to-nextcloud\>/apps/workflow_script* contents with contents in *./data/workflow_script* (including all hidden files)

  

## TODO How to execute
* all executable scripts are in *./bin* folder
    * .py must be executed with python interpreter and appropriate config file path from *./config* must be set as parameter
* there is usage print when you run script without correct parameters

TODO:
* if you are planning to run archivation and validation worker remotly from file storage:
    * setup sftp connection - create keys etc...
    * setup login only using keys
    * setup proper data to configs
    * ensure that user which is used for remote login has access rigths to given directories

### Config formats
* Inside all config examples are comments explaining different fields
* All workers have defined their own configs
* db_config part can be formated by this -> https://dev.mysql.com/doc/connector-python/en/connector-python-connectargs.html

### TODO Task Scripts

| name                   | purpose                                                                                                                           |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| make_archivation_task.py    | Manual creation of task for archivation of given file                                                                             |
| retimestamping_task.py | Regular checking of timestamps expiration dates in database and creating a task for those which validity is ending within 24 ours |
| validation_task.py     | Interactive interface for creating tasks for validation of archived files                                                         |



### TODO Workers

| name                     | purpose                                                   |
| ------------------------ | --------------------------------------------------------- |
| archivation_worker.py    | responsible for consuming archivation tasks from rabbitmq |
| retimestamping_worker.py | responsible for consuming tasks for retimestamping        |
| validation_worker.py     | responsible for validation of archived files              |

