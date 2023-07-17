from flask import Blueprint, redirect
from website import CONFIG

printlabels = Blueprint('printlabels', __name__)

@printlabels.route('/printLabels', methods=['GET', 'POST'])
def print_labels():
    '''
    Generate template html page code
    Should redirect to the page for the template generator (sub-tree) with LFNL config.
    The redirect below doesn't work but serves as a reminder for later.
    '''

    return redirect(CONFIG['label_printing']['url'])
