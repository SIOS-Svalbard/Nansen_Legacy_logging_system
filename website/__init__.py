from flask import Flask
import uuid
from website.database.init_db import run as init_db

DBNAME = 'testdb'
METADATA_CATALOGUE = "testcruise"

# Initialising the database
init_db(DBNAME, METADATA_CATALOGUE)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = str(uuid.uuid1())

    from .views import views

    app.register_blueprint(views, url_prefix='/')

    return app
