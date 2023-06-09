from flask import Blueprint, render_template, request, send_file, redirect

generatetemplates = Blueprint('generatetemplates', __name__)

@generatetemplates.route('/generateTemplate', methods=['GET', 'POST'])
def generate_template():
    '''
    Generate template html page code
    Should redirect to the page for the template generator (sub-tree) with LFNL config.
    The redirect below doesn't work but serves as a reminder for later.
    '''

    return redirect("/config=Learnings from Nansen Legacy logging system")
