from flask import Blueprint, redirect
from website import CONFIG

generatetemplates = Blueprint('generatetemplates', __name__)

@generatetemplates.route('/generateTemplate', methods=['GET', 'POST'])
def generate_template():
    '''
    Generate template html page code
    Should redirect to the page for the template generator (sub-tree) with LFNL config.
    The redirect below doesn't work but serves as a reminder for later.
    '''

    return redirect(CONFIG['template_generator']['url'])
