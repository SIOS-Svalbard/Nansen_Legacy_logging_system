from flask import Blueprint, redirect, render_template, session, request
from website import CONFIG, FIELDS_FILEPATH
from website.lib.get_dict_for_list_of_fields import get_dict_for_list_of_fields

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

    if request.method == 'GET':

        return render_template(
        "printLabelsForIDs.html",
        ids = ids,
        possible_fields_dict = possible_fields_dict
        )

    if request.method == 'POST':

        ids = request.form.get('ids')  # Retrieve the IDs from the form
        ids_list = ids.split('\r\n')  # Split the IDs into a list using newline character
        labelType = request.form.get('labelType')

        return render_template(
        "printLabelsForIDs.html",
        ids = ids_list,
        possible_fields_dict = possible_fields_dict
        )
