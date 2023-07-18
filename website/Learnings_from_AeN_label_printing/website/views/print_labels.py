from flask import Blueprint, render_template, flash, request
from website import CONFIG
from website.lib.add_one_to_numbers_in_string import add_one_to_numbers_in_string
from website.lib.create_labels import create_medium, create_large
from website.lib.interact_with_printer import try_to_connect_to_printer, cancel_print, send_label_to_printer
import uuid

print_labels = Blueprint('print_labels', __name__)

@print_labels.route('/print_medium_labels', methods=['GET', 'POST'])
def print_medium_labels():

    size = 'medium'
    ribbon = 'Zebra 5095, 84 mm'
    labels = 'CILS Eppendorf, 81000TN'
    ip = CONFIG['medium_label_printer']['ip']

    increment3 = False
    increment4 = False
    number_labels = 1

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

    if request.method == "GET":

        return render_template(
        "/print_labels.html",
        size=size,
        ribbon=ribbon,
        labels=labels,
        ip=ip,
        text=text,
        increment3=increment3,
        increment4=increment4,
        number_labels=number_labels
        )

    elif request.method == "POST":

        form_input = request.form.to_dict(flat=False)

        (
            number_labels,
            ip,
            text,
            increment3,
            increment4
        ) = get_values_from_form(text, form_input)

        good, errors = try_to_connect_to_printer(ip)

        if good == False:

            for error in errors:
                flash(error, category='error')

            return render_template(
            "/print_labels.html",
            size=size,
            ribbon=ribbon,
            labels=labels,
            ip=ip,
            text=text,
            increment3=increment3,
            increment4=increment4,
            number_labels=number_labels
            )

        else:

            if "cancel" in form_input:
                cancel_print()
                flash('All jobs on printer cancelled', category='success')

                return render_template(
                "/print_labels.html",
                size=size,
                ribbon=ribbon,
                labels=labels,
                ip=ip,
                text=text,
                increment3=increment3,
                increment4=increment4,
                number_labels=number_labels
                )
            else:

                text = increment_and_print_all(
                    number_labels,
                    ip,
                    text,
                    increment3,
                    increment4,
                    size
                )

                return render_template(
                "/print_labels.html",
                size=size,
                ribbon=ribbon,
                labels=labels,
                ip=ip,
                text=text,
                increment3=increment3,
                increment4=increment4,
                number_labels=number_labels
                )

@print_labels.route('/print_large_labels', methods=['GET', 'POST'])
def print_large_labels():

    size = 'large'
    ribbon = 'BRADY R-6400, 65 mm'
    labels = 'BRADY 48.26 × 25.4 mm ,THT-156-492-1.5-SC'
    ip = CONFIG['large_label_printer']['ip']

    increment3 = False
    increment4 = False
    number_labels = 1

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

    if request.method == "GET":

        return render_template(
        "/print_labels.html",
        size=size,
        ribbon=ribbon,
        labels=labels,
        ip=ip,
        text=text,
        increment3=increment3,
        increment4=increment4,
        number_labels=number_labels
        )

    elif request.method == "POST":

        form_input = request.form.to_dict(flat=False)

        (
            number_labels,
            ip,
            text,
            increment3,
            increment4
        ) = get_values_from_form(text, form_input)

        good, errors = try_to_connect_to_printer(ip)

        if good == False:

            for error in errors:
                flash(error, category='error')

            return render_template(
            "/print_labels.html",
            size=size,
            ribbon=ribbon,
            labels=labels,
            ip=ip,
            text=text,
            increment3=increment3,
            increment4=increment4,
            number_labels=number_labels
            )

        else:

            if "cancel" in form_input:
                cancel_print()
                flash('All jobs on printer cancelled', category='success')

                return render_template(
                "/print_labels.html",
                size=size,
                ribbon=ribbon,
                labels=labels,
                ip=ip,
                text=text,
                increment3=increment3,
                increment4=increment4,
                number_labels=number_labels
                )
            else:

                text = increment_and_print_all(
                    number_labels,
                    ip,
                    text,
                    increment3,
                    increment4,
                    size
                )

                return render_template(
                "/print_labels.html",
                size=size,
                ribbon=ribbon,
                labels=labels,
                ip=ip,
                text=text,
                increment3=increment3,
                increment4=increment4,
                number_labels=number_labels
                )

def get_values_from_form(text, form_input):
    '''
    Retrieve values from form.
    These values are preserved after the user hits print.
    '''
    number_labels = form_input['number_labels'][0]
    ip = form_input['ip'][0]
    for line, criteria in text.items():
        text[line]['content'] = form_input[f'line{line}'][0]
    if 'increment3' in form_input and form_input['increment3'] == ['on']:
        increment3 = True
    else:
        increment3 = False
    if 'increment4' in form_input and form_input['increment4'] == ['on']:
        increment4 = True
    else:
        increment4 = False
    return number_labels, ip, text, increment3, increment4

def increment_and_print_all(number_labels,ip,text,increment3,increment4,size):
    number_labels = int(number_labels)
    for n in range(number_labels):

        if 'size' == 'large':
            zpl = create_large(
                str(uuid.uuid4()),
                text[1]['content'],
                text[2]['content'],
                text[3]['content'],
                text[4]['content'],
                text[5]['content']
                )
        elif 'size' == 'medium':
            zpl = create_medium(
                str(uuid.uuid4()),
                text[1]['content'],
                text[2]['content'],
                text[3]['content'],
                text[4]['content']
                )

        send_label_to_printer(zpl)

        if increment3 == True:
            text[3]['content'] = add_one_to_numbers_in_string(text[3]['content'])
        if increment4 == True:
            text[4]['content'] = add_one_to_numbers_in_string(text[4]['content'])

    return text
