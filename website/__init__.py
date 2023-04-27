from flask import Flask
import uuid
from website.lib.init_db import run as init_db
from website.lib.init_cruise_tables import run as init_cruise_tables
from website.lib.get_data import get_cruise
import pandas as pd
import json
import os

BASE_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

with open(os.path.join(BASE_PATH, "config.json"), "r") as fp:
    CONFIG = json.load(fp)

# Create the database if it doesn't already exist
DB = CONFIG["database"]
init_db(DB)
DBNAME = DB["dbname"]

#TOKTLOGGER = '172.16.0.210' # IP of VM of toktlogger"
#TOKTLOGGER = 'toktlogger-sars.hi.no'
TOKTLOGGER = CONFIG["toktlogger"]["host"]
if TOKTLOGGER:
    url = f"http://{TOKTLOGGER}/api/cruises/current?format=json"
else:
    url = None

BTL_FILES_FOLDER = CONFIG["niskinBottles"]["dir"]

# GET CRUISE DETAILS, RETURNS FALSE IF NO CRUISE
cruise_details_df = get_cruise(DB)

if isinstance(cruise_details_df, pd.DataFrame):
    CRUISE_NUMBER = cruise_details_df['cruise_number'].item()
    VESSEL_NAME = cruise_details_df['vessel_name'].item()
    METADATA_CATALOGUE = 'metadata_catalogue_'+str(CRUISE_NUMBER)
    init_cruise_tables(DB, CRUISE_NUMBER, VESSEL_NAME)
else:
    CRUISE_NUMBER = None
    VESSEL_NAME = None
    METADATA_CATALOGUE = None

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
    from .exportdata import exportdata

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(registrations, url_prefix='/')
    app.register_blueprint(logsamples, url_prefix='/')
    app.register_blueprint(generatetemplates, url_prefix='/')
    app.register_blueprint(submitspreadsheets, url_prefix='/')
    app.register_blueprint(missingmetadata, url_prefix='/')
    app.register_blueprint(choosesamplefields, url_prefix='/')
    app.register_blueprint(logsamplesform, url_prefix='/')
    app.register_blueprint(exportdata, url_prefix='/')

    return app
