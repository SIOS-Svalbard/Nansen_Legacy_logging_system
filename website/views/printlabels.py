from flask import Blueprint, redirect, render_template
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

    return render_template(
    "printLabelsForIDs.html"
    )
