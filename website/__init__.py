from flask import Flask
import uuid
import os.path
import json

BASE_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
with open(os.path.join(BASE_PATH, "config.json"), "r") as fp:
    CONFIG = json.load(fp)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = str(uuid.uuid4())

    from .views.home import home
    from .views.print_labels import print_labels
    from .views.uuid_generator import uuid_generator
    from .views.data_matrices_pdf import data_matrices_pdf

    app.register_blueprint(home, url_prefix='/')
    app.register_blueprint(print_labels, url_prefix='/')
    app.register_blueprint(uuid_generator, url_prefix='/')
    app.register_blueprint(data_matrices_pdf, url_prefix='/')

    return app
