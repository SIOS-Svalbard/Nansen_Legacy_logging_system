# Nansen Legacy logging system

The Nansen Legacy logging system, designed based on experiences gained during the Nansen Legacy project (Arven etter Nansen - AeN). Metadata logging system to be deployed on vessels, to log multidisciplinary marine data.

The software is a locally-hosted Flask Python web server that should be deployed on a virtual machine. Users access a GUI via an IP address (or DNS?) when plugged into the network. Metadata related to onboard activities and samples are logged in a PostgreSQL database table.

Metadata are logged in a hierarchical way. Metadata related to activities sit at the top of the pyramid, and  are pulled from the API of an onboard 'Toktlogger' developed by the Institute of Marine Research. Metadata related to Niskin bottles are pulled from .btl files stored on the network. Samples must be logged manually by the users.  

This work is a development of the Nansen Legacy labelling system, developed Pål Ellingsen and colleagues:
https://github.com/SIOS-Svalbard/AeN_data
https://github.com/SIOS-Svalbard/darwinsheet
Paper: https://doi.org/10.5334/DSJ-2021-034

## Setup and Installation

This application was developed with Python version 3.8.10, and PostgreSQL version 9.4.26

```
git clone <repo-url>

pip install -r requirements.txt
```

Edit the config.json file to suit your local configuration.

You can visit this site to install PostgreSQL: https://www.postgresql.org/download/

The software is configured to run using the *postgres* user. The password might be *postgres* by default. However, if you get an error like

`FATAL:  password authentication failed for user "postgres"`

then you need to change the password. For example, for Linux users:

```
sudo -u postgres -i                          # Log into postgres user
psql                                         # Open PostgreSQL
ALTER USER postgres PASSWORD 'new_password';
\q                                           # exit psql
exit                                         # exit PostgreSQL user's shell
```

Specify your configuration in the `config.json` file.

## Running the application

The application can be run using WSGI (flaskapp.wsgi) and has been developed using apache2.

Alternatively, it can be launched for testing and development purposes by running

```
./main.py
```

## Run application using docker-compose

> [!CAUTION]
> In the provided configuration, the postgres database is also ran in a docker container.
> This is not recommended in a production environment due to the risk of data loss.

A running Docker daemon is needed. Ensure Docker is installed and the Docker service is running on your machine.

Docker Compose is required. Make sure Docker Compose is installed and available in your system's PATH.

Create an empty folder named `nl_logger_postgres_data/data`, if you plan on running the database in a container.
You will also need to adapt `database.host` field in the `config.json` file:
```
{
  "database": {
    "host": "postgres",
    "user": "postgres",
    "password": "postgres",
    "dbname": "nl_db"
  },
  ...
```

You might want to modify the `docker-compose.yaml` file, especially the ports.

Following command will download, build the necessary images and create and launch the containers.
```
docker compose up -d
```

## Viewing the application

Go to http://127.0.0.1:5001 in your web browser, or wherever you have set up the logging system to be hosted if running as a WSGI application.

## Subtrees

The logging system has two subtrees:

* Nansen Legacy label printing: For printing labels. Labels can be printed to include text taken from fields used in the logging system.
	- https://github.com/SIOS-Svalbard/Nansen_Legacy_label_printing
* Nansen Legacy template generator: For generating Excel templates. Spreadsheets can be configured based on the type of sample being logged in the logging system, and logged (meta)data can also be exported to a template.
	- https://github.com/SIOS-Svalbard/Nansen_Legacy_template_generator
