from flask import Flask, session
import uuid
from website.lib.init_db import run as init_db
from website.lib.init_cruise_tables import run as init_cruise_tables
from website.lib.get_data import get_cruise
from website.lib.get_dict_for_list_of_fields import get_dict_for_list_of_fields
import pandas as pd
import json
import os

BASE_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
CONFIG_PATH = os.path.join(BASE_PATH, 'website', 'Nansen_Legacy_template_generator', 'website', 'config', 'template_configurations.yaml')

with open(os.path.join(BASE_PATH, "config.json"), "r") as fp:
    CONFIG = json.load(fp)

# Create the database if it doesn't already exist
DB = CONFIG["database"]
init_db(DB)
DBNAME = DB["dbname"]

TOKTLOGGER = CONFIG["toktlogger"]["host"]
if TOKTLOGGER == "":
    url = None
elif TOKTLOGGER:
    url = f"http://{TOKTLOGGER}/api/cruises/current?format=json"
else:
    url = None

BTL_FILES_FOLDER = CONFIG["niskinBottles"]["dir"]
FIELDS_FILEPATH = os.path.join(BASE_PATH, 'website', 'Nansen_Legacy_template_generator', 'website', 'config', 'fields')

# GET CRUISE DETAILS, RETURNS NONE IF NO CRUISE
cruise_details_df = get_cruise(DB)

if cruise_details_df is not None:
    CRUISE_NUMBER = cruise_details_df['cruise_number'].item()
    VESSEL_NAME = cruise_details_df['vessel_name'].item()
    METADATA_CATALOGUE = 'metadata_catalogue_'+str(CRUISE_NUMBER)
else:
    CRUISE_NUMBER = None
    VESSEL_NAME = None
    METADATA_CATALOGUE = None

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = str(uuid.uuid4())

    from .views.home import home
    from .views.setupcruise import setupcruise
    from .views.registrations import registrations
    from .views.logsamples import logsamples
    from .views.generatetemplates import generatetemplates
    from .views.printlabels import printlabels
    from .views.uploaddata import uploaddata
    from .views.missingmetadata import missingmetadata
    from .views.choosesamplefields import choosesamplefields
    from .views.chooseactivityfields import chooseactivityfields
    from .views.logsamplesform import logsamplesform
    from .views.exportdata import exportdata

    app.register_blueprint(home, url_prefix='/')
    app.register_blueprint(setupcruise, url_prefix='/')
    app.register_blueprint(registrations, url_prefix='/')
    app.register_blueprint(logsamples, url_prefix='/')
    app.register_blueprint(generatetemplates, url_prefix='/')
    app.register_blueprint(printlabels, url_prefix='/')
    app.register_blueprint(uploaddata, url_prefix='/')
    app.register_blueprint(missingmetadata, url_prefix='/')
    app.register_blueprint(choosesamplefields, url_prefix='/')
    app.register_blueprint(chooseactivityfields, url_prefix='/')
    app.register_blueprint(logsamplesform, url_prefix='/')
    app.register_blueprint(exportdata, url_prefix='/')

    @app.context_processor
    def inject_ids_to_print():
        # Retrieve the list of IDs from the session
        ids_to_print = session.get('ids_to_print')

        return dict(ids_to_print=ids_to_print)

    return app
