from flask import Blueprint, render_template, flash
from website import CONFIG


print_labels = Blueprint('print_labels', __name__)

@print_labels.route('/print_medium_labels', methods=['GET', 'POST'])
def print_medium_labels():

    size = 'medium'
    ribbon = 'Zebra 5095, 84 mm'
    labels = 'CILS Eppendorf, 81000TN'
    ip = CONFIG['medium_label_printer']['ip']

    text = {
        1: { # Line 1
            'max_number_of_characters': 18,
            'content': ''
        },
        2: { # Line 2
            'max_number_of_characters': 18,
            'content': ''
        },
        3: { # Line 3
            'max_number_of_characters': 18,
            'content': ''
        },
        4: { # Line 4
            'max_number_of_characters': 18,
            'content': ''
        }
    }

    return render_template(
    "/print_labels.html",
    size=size,
    ribbon=ribbon,
    labels=labels,
    ip=ip,
    text=text
    )

@print_labels.route('/print_large_labels', methods=['GET', 'POST'])
def print_large_labels():

    size = 'large'
    ribbon = 'BRADY R-6400, 65 mm'
    labels = 'BRADY 48.26 × 25.4 mm ,THT-156-492-1.5-SC'
    ip = CONFIG['large_label_printer']['ip']

    text = {
        1: { # Line 1
            'max_number_of_characters': 20,
            'content': ''
        },
        2: { # Line 2
            'max_number_of_characters': 20,
            'content': ''
        },
        3: { # Line 3
            'max_number_of_characters': 20,
            'content': ''
        },
        4: { # Line 4
            'max_number_of_characters': 26,
            'content': ''
        },
        5: { # Line 5
            'max_number_of_characters': 26,
            'content': ''
        }
    }

    return render_template(
    "/print_labels.html",
    size=size,
    ribbon=ribbon,
    labels=labels,
    ip=ip,
    text=text
    )
