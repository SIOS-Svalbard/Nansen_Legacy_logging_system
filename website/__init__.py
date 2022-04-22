from flask import Flask
import uuid
from website.database.init_db import run as init_db

DBNAME = 'testdb'
CRUISE_NUMBER = 12345678

METADATA_CATALOGUE = 'metadata_catalogue_'+str(CRUISE_NUMBER)
CRUISE_DETAILS_TABLE = 'cruise_details_'+str(CRUISE_NUMBER)

# Initialising the database
init_db(DBNAME, CRUISE_NUMBER, METADATA_CATALOGUE, CRUISE_DETAILS_TABLE)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = str(uuid.uuid1())

    from .views import views

    app.register_blueprint(views, url_prefix='/')

    return app
