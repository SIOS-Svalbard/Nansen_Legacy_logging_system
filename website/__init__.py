from flask import Flask
import uuid

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = str(uuid.uuid4())

    from .views.home import home

    app.register_blueprint(home, url_prefix='/')

    return app
