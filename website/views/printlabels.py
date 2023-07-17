from flask import Blueprint, redirect, render_template, session
from website import CONFIG

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
    Print labels for samples already registered based on ID and fields
    '''
    # Retrieve the list of IDs from the session
    ids = session.get('ids_to_print')

    # Clear the session variable to avoid data persisting across requests
    #session.pop('ids', None)

    return render_template(
    "printLabelsForIDs.html",
    ids = ids
    )
