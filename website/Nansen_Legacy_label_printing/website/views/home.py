from flask import Blueprint, render_template, flash

home = Blueprint('home', __name__)

@home.route('/', methods=['GET'])
def homepage():

    return render_template(
    "home.html"
    )
