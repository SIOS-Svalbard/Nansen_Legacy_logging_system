import os
from flask import Flask
import uuid
from website.database.init_db import run as init_db
import requests
import numpy as np

TOKTLOGGER = '172.16.1.90' # VM of toktlogger at UNIS on my laptop"
VESSEL_NAME = 'Kronprins Haakon'
url = "http://"+TOKTLOGGER+"/api/cruises/current?format=json"
DBNAME = 'lfnl_db'

#BTL_FILES_FOLDER = '/home/lukem/Documents/Testing/btl_files/'
BTL_FILES_FOLDER = f"C:{os.sep}Vitaly_dir{os.sep}HI_docs{os.sep}Nansen_Legacy{os.sep}data{os.sep}2021708{os.sep}"
TMP_FILES_FOLDER = f"C:{os.sep}Vitaly_dir{os.sep}tmp"

DB = {"host": "localhost", "dbname": '', "user": '', "password": ''}
try:
    response = requests.get(url)
    json_cruise = response.json()

    CRUISE_NUMBER = json_cruise['cruiseNumber']
    VESSEL_NAME = json_cruise['vesselName']

except:
    print('\nCould not connect to the Toktlogger\n')
    print('Please provide details to initialise the database for cruise.')
    print('These details will be used to name the tables in the PSQL database')

    '''
    Need to find a better way to manage when Toktlogger offline.
    This current solution will prompt the user to input details below each time
    this script runs.
    A new table for the metadata catalogue will be created every time a different
    cruise number is given.
    Old activities and samples will disappear from the GUI - stored in different
    tables in the database
    Need to find a way of storing cruise number once given, to use every time
    for the remainder of the current cruise only.
    '''
    CRUISE_NUMBER = input("CRUISE NUMBER > ")
    DB["dbname"] = input("DB name > ")
    DB["user"] = input("DB user > ")
    DB["password"] = input("DB password > ")

print(f"CRUISE_NUMBER:{CRUISE_NUMBER}, DB:{DB}")

METADATA_CATALOGUE = 'metadata_catalogue_'+str(CRUISE_NUMBER)
CRUISE_DETAILS_TABLE = 'cruise_details_'+str(CRUISE_NUMBER)

# Initialising the database
#init_db(DBNAME, CRUISE_NUMBER, METADATA_CATALOGUE, CRUISE_DETAILS_TABLE)
init_db(DB, CRUISE_NUMBER, METADATA_CATALOGUE, CRUISE_DETAILS_TABLE)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = str(uuid.uuid1())

    from .views import views
    from .registrations import registrations
    from .logsamples import logsamples
    from .generatetemplates import generatetemplates
    from .submitspreadsheets import submitspreadsheets
    from .missingmetadata import missingmetadata
    from .choosesamplefields import choosesamplefields
    from .logsamplesform import logsamplesform

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(registrations, url_prefix='/')
    app.register_blueprint(logsamples, url_prefix='/')
    app.register_blueprint(generatetemplates, url_prefix='/')
    app.register_blueprint(submitspreadsheets, url_prefix='/')
    app.register_blueprint(missingmetadata, url_prefix='/')
    app.register_blueprint(choosesamplefields, url_prefix='/')
    app.register_blueprint(logsamplesform, url_prefix='/')

    return app
