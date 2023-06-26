# Learnings from AeN logging system

Learnings from AeN logging system designed based on experiences gained during the Nansen Legacy project (Arven etter Nansen - AeN). Metadata logging system to be deployed on vessels, to log multidisciplinary marine data.

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

## Running the application

```
./main.py
```

## Viewing the application

Go to http://127.0.0.1:5001 in your web browser
