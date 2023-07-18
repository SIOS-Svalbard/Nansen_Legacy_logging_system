from flask import Blueprint, redirect, render_template, session, request, flash
from website import DB, CONFIG, FIELDS_FILEPATH
from website.lib.get_dict_for_list_of_fields import get_dict_for_list_of_fields
from website.lib.get_data import get_metadata_for_list_of_ids, get_cruise, get_all_ids
import copy
from website.Learnings_from_AeN_label_printing.website.lib.create_labels import create_medium, create_large
from website.Learnings_from_AeN_label_printing.website.lib.interact_with_printer import try_to_connect_to_printer, cancel_print, send_label_to_printer
from website.Learnings_from_AeN_label_printing.website.lib.add_one_to_numbers_in_string import add_one_to_numbers_in_string

printlabels = Blueprint('printlabels', __name__)

@printlabels.route('/printLabels', methods=['GET', 'POST'])
def print_labels():
    '''
    Generate template html page code
    Should redirect to the page for the label printing repo (sub-tree).
    '''

    return redirect(CONFIG['label_printing']['url'])

@printlabels.route('/printLabelsForIDs', methods=['GET', 'POST'])
def print_labels_for_ids():
    '''
    Generate template html page code
    Select IDs and label type for samples already registered
    '''
    # Retrieve the list of IDs from the session
    ids = session.get('ids_to_print')

    # Clear the session variable to avoid data persisting across requests
    session.pop('ids', None)

    if not ids:
        ids = ['']

    possible_fields_to_print = [
        "catalogNumber",
        "bottleNumber",
        "eventDate",
        "eventTime",
        "stationName",
        "statID",
        "decimalLatitude",
        "decimalLongitude",
        "sampleType",
        "gearType",
        "pi_name",
        "pi_email",
        "pi_institution",
        "pi_orcid",
        "recordedBy_name",
        "recordedBy_email",
        "recordedBy_institution",
        "recordedBy_orcid",
        "minimumDepthInMeters",
        "maximumDepthInMeters",
        "minimumElevationInMeters",
        "maximumElevationInMeters"
    ]

    possible_fields_dict = get_dict_for_list_of_fields(possible_fields_to_print,FIELDS_FILEPATH)

    lines = {}
    for l in range(5):
        lines[l] = {
            'value': ''
        }
        if l in [3,4]:
            lines[l]['character_limit'] = 26
        else:
            lines[l]['character_limit'] = 20
    labelType = 'large'

    if request.method == 'GET':

        return render_template(
        "printLabelsForIDs.html",
        ids = ids,
        possible_fields_dict = possible_fields_dict,
        lines = lines,
        labelType = labelType
        )

    if request.method == 'POST':

        ids = request.form.get('ids')  # Retrieve the IDs from the form
        ids_list = ids.split('\r\n')  # Split the IDs into a list using newline character

        labelType = request.form.get('labelType')

        form_input = request.form.to_dict(flat=False)
        num_lines = 0
        if labelType == 'medium':
            max_num_lines = 4
            ip = CONFIG['label_printing']['medium_label_printer']['ip']
        elif labelType == 'large':
            max_num_lines = 5
            ip = CONFIG['label_printing']['medium_label_printer']['ip']

        good, errors = try_to_connect_to_printer(ip)
        #good = True
        #errors = []

        fields_to_include = []
        for field, vals in possible_fields_dict.items():
            if field in form_input and form_input[field] == ['y']:
                num_lines = num_lines + 1
                possible_fields_dict[field]['checked'] = ['y']
                fields_to_include.append(field.lower())

        long_lines = []

        for num, criteria in lines.items():
            lines[num]['value'] = request.form.get(f'line{num}')
            if lines[num]['value'] != '':
                num_lines = num_lines + 1
                if labelType == 'medium' and num == 4:
                    errors.append("Don't use the 5th line for medium labels. Only 4 lines allowed")
                    good = False
            if labelType == 'medium':
                max_length = 18
                if len(lines[num]['value']) > max_length:
                    long_lines.append(num+1)
            if f'increment{num}' in form_input and form_input[f'increment{num}'] == ['y']:
                criteria['increment'] = 'y'

        if len(long_lines) > 0:
            good = False
            errors.append(f"Lines can't be more than 18 characters long for medium labels: Lines {long_lines}")

        if num_lines > max_num_lines:
            good = False
            errors.append(f'{num_lines} fields/lines selected/entered. Please include a maximum of {max_num_lines} for {labelType} labels.')

        cruise_details_df = get_cruise(DB)
        CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

        all_ids = get_all_ids(DB, CRUISE_NUMBER)
        ids_not_recognised = []
        for id in ids_list:
            if id not in all_ids and id != '':
                ids_not_recognised.append(id)

        if len(ids_not_recognised) > 0:
            errors.append(f'ID(s) not registered in the system. Check for typos or unwanted whitespace. IDs: {ids_not_recognised}')
            good=False

        if len(ids_list) == 1 and ids_list[0] == '':
            good = False
            errors.append('Please enter at least 1 ID into the box')

        if good == False:
            for error in errors:
                flash(error, category='error')

        else:

            if "cancel" in form_input:
                cancel_print()
                flash('All jobs on printer cancelled', category='success')

                return render_template(
                "printLabelsForIDs.html",
                ids = ids_list,
                possible_fields_dict = possible_fields_dict,
                lines = lines,
                labelType = labelType
                )
            else:

                # Retrieve metadata for IDs
                df_samples = get_metadata_for_list_of_ids(DB, CRUISE_NUMBER, ids_list)

                # Write lines and selected fields to dictionary, clip lines if neccessary
                n = 0
                for idx, row in df_samples.iterrows():

                    text_to_print = copy.deepcopy(lines)

                    for col in df_samples.columns:
                        if col in fields_to_include:
                            for key, vals in text_to_print.items():
                                val_to_write = str(row[col])
                                if val_to_write in [None, 'NULL', 'None']:
                                    val_to_write = ''
                                if labelType == 'medium':
                                    character_limit = 18
                                elif labelType == 'large':
                                    character_limit = lines[key]['character_limit']
                                if len(val_to_write) > character_limit:
                                    val_to_write = val_to_write[:character_limit]
                                if vals['value'] in ['',val_to_write]:
                                    vals['value'] = val_to_write
                                    break

                    id = ids_list[n]
                    n = n + 1

                    if labelType == 'large':
                        zpl = create_large(
                            str(id),
                            text_to_print[0]['value'],
                            text_to_print[1]['value'],
                            text_to_print[2]['value'],
                            text_to_print[3]['value'],
                            text_to_print[4]['value']
                            )
                    elif 'size' == 'medium':
                        zpl = create_medium(
                            str(id),
                            text_to_print[0]['value'],
                            text_to_print[1]['value'],
                            text_to_print[2]['value'],
                            text_to_print[3]['value']
                            )

                    try:
                        send_label_to_printer(zpl)
                    except:
                        flash(f'Printing failed for ID {id}', category='error')

                    for num, criteria in lines.items():
                        if f'increment{num}' in form_input and form_input[f'increment{num}'] == ['y']:
                            criteria['value'] = add_one_to_numbers_in_string(criteria['value'])

                flash('Printing complete', category='success')

        return render_template(
        "printLabelsForIDs.html",
        ids = ids_list,
        possible_fields_dict = possible_fields_dict,
        lines = lines,
        labelType = labelType
        )
