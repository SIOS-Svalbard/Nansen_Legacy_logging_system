# Learnings from Nansen Legacy logging system

Learnings from Nansen Legacy logging system, designed based on experiences gained during the Nansen Legacy project (Arven etter Nansen - AeN). Metadata logging system to be deployed on vessels, to log multidisciplinary marine data.

The software is a locally-hosted Flask Python web server that should be deployed on a virtual machine. Users access a GUI via an IP address (or DNS?) when plugged into the network. Metadata related to onboard activities and samples are logged in a PostgreSQL database table.

Metadata are logged in a hierarchical way. Metadata related to activities sit at the top of the pyramid, and  are pulled from the API of an onboard 'Toktlogger' developed by the Institute of Marine Research. Metadata related to Niskin bottles are pulled from .btl files stored on the network. Samples must be logged manually by the users.  

This work is a development of the Nansen Legacy labelling system, developed Pål Ellingsen and colleagues:
https://github.com/SIOS-Svalbard/AeN_data
https://github.com/SIOS-Svalbard/darwinsheet
https://doi.org/10.5334/DSJ-2021-034

## Setup and Installation

This application was developed with Python version 3.8.10, and PostgreSQL version 9.4.26

```
git clone <repo-url>

pip install -r requirements.txt
```

Edit the config.json file to suit your local configuration.

## Running the application

The application can be run using WSGI (flaskapp.wsgi) and has been developed using apache2.

Alternatively, it can be launched by running

```
./main.py
```

## Viewing the application

Go to http://127.0.0.1:5001 in your web browser, or wherever you have set up the logging system to be hosted if running as a WSGI application.

## Subtrees

The logging system has two subtrees.

* Learnings from Nansen Legacy label printing: For printing labels. Labels can be printed to include text taken from fields used in the logging system.
	- https://github.com/SIOS-Svalbard/Learnings_from_AeN_label_printing
* Learnings from Nansen Legacy template generator: For generating Excel templates. Spreadsheets can be configured based on the type of sample being logged in the logging system, and logged (meta)data can also be exported to a template.
	- https://github.com/SIOS-Svalbard/Learnings_from_AeN_template_generator
