from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from website.lib.create_template_for_registering_personnel import create_personnel_template
from website.lib.register_personnel_from_file import register_personnel_from_file
from website.lib.get_data import get_data, get_cruise, get_cruise_details, get_personnel_list, get_projects_list
from website import DB
import psycopg2
from website.lib.other_functions import split_personnel_list
import uuid

setupcruise = Blueprint('setupcruise', __name__)

@setupcruise.route('/setupCruise/uploadPersonnel', methods=['GET', 'POST'])
def uploadpersonnel():

    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

    df = get_data(DB, 'personnel_'+CRUISE_NUMBER)
    df.sort_values(by='last_name', inplace=True)
    first_names = list(df['first_name'])
    last_names = list(df['last_name'])
    emails = list(df['email'])
    orcids = list(df['orcid'])
    institutions = list(df['institution'])
    comments = list(df['comment'])

    if request.method == 'POST':
        form_input = request.form.to_dict(flat=False)

        if 'submit' in form_input.keys() and form_input['submit'] == ['skipPersonnel']:
            return redirect('/setupCruise/cruiseDetails')

        elif 'submit' in form_input.keys() and form_input['submit'] == ['skipRestOfSetup']:
            return redirect('/')

        elif 'submit' in form_input.keys() and form_input['submit'] == ['generateExcel']:
            filepath = f'/tmp/template_for_registering_personnel.xlsx'

            create_personnel_template(filepath)

            return send_file(filepath, as_attachment=True)

        elif 'submit' in form_input.keys() and form_input['submit'] == ['submitExcel']:

            f = request.files['file']

            good, errors = register_personnel_from_file(f)

            if good == False:
                for error in errors:
                    flash(error, category='error')
            else:
                flash('Personnel uploaded successfully')
                return redirect('/setupCruise/cruiseDetails')

    return render_template(
    "setupCruise/setupCruisePersonnel.html",
    first_names=first_names,
    last_names = last_names,
    emails = emails,
    institutions = institutions,
    orcids=orcids,
    comments=comments,
    len=len(first_names)
    )

@setupcruise.route('/setupCruise/cruiseDetails', methods=['GET', 'POST'])
def cruisedetails():

    (
    CRUISE_NUMBER,
    cruise_name,
    project,
    cruise_leader,
    cocruise_leader,
    comment,
    ) = get_cruise_details(DB)

    personnel = get_personnel_list(DB, CRUISE_NUMBER, 'personnel_'+CRUISE_NUMBER)
    projects = get_projects_list(DB)
    newProject = ''

    if request.method == 'POST':

        # Getting data from form
        newProject = request.form.get('newProject').capitalize()
        project = request.form.get('project').capitalize()
        cruise_name = request.form.get('cruiseName').capitalize()
        comment = request.form.get('comment')
        cruise_leader = request.form.get('cruiseLeader')
        cocruise_leader = request.form.get('coCruiseLeader')

        df_personnel = get_data(DB, 'personnel_'+CRUISE_NUMBER)
        (
        cruise_leader_name,
        cruise_leader_email,
        cruise_leader_orcid,
        cruise_leader_institution
        ) = split_personnel_list(cruise_leader, df_personnel)
        (
        cocruise_leader_name,
        cocruise_leader_email,
        cocruise_leader_orcid,
        cocruise_leader_institution
        ) = split_personnel_list(cocruise_leader, df_personnel)

        # Validations
        good = True
        errors = []

        if project == '' and newProject == '':
            good = False
            errors.append('Please select a project or register a new one')
        elif project == '' and newProject != '':
            project_to_register = newProject
        elif project != '' and newProject != '':
            good = False
            errors.append('Either select a project or register a new one, not both.')
        else:
            project_to_register = project

        if newProject in projects:
            good = False
            errors.append('Project with same full name already registered. Select it from the drop-down list')
        elif len(newProject) < 7 and project == '':
            good = False
            errors.append('Project name must be at least 7 characters long')

        if good == False:
            for error in errors:
                flash(error, category='error')

        else:
            if newProject != '':
                conn = psycopg2.connect(**DB)
                cur = conn.cursor()

                cur.execute(f"INSERT INTO projects (id, project, created) VALUES ('{uuid.uuid4()}', '{project_to_register}', CURRENT_TIMESTAMP);")

                conn.commit()
                cur.close()
                conn.close()

                flash('Project registered!', category='success')

            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            cur.execute(f'''UPDATE cruises SET
            cruise_name = '{cruise_name}',
            project = '{project_to_register}',
            cruise_leader_orcid = '{cruise_leader_orcid}',
            cruise_leader_name = '{cruise_leader_name}',
            cruise_leader_institution = '{cruise_leader_institution}',
            cruise_leader_email = '{cruise_leader_email}',
            co_cruise_leader_orcid = '{cocruise_leader_orcid}',
            co_cruise_leader_name = '{cocruise_leader_name}',
            co_cruise_leader_institution = '{cocruise_leader_institution}',
            co_cruise_leader_email = '{cocruise_leader_email}',
            comment = '{comment}'
            WHERE cruise_number = '{CRUISE_NUMBER}';
            ''')

            conn.commit()
            cur.close()
            conn.close()

            flash('Cruise details registered!', category='success')

            return redirect('/')

    return render_template(
    "setupCruise/setupCruiseDetails.html",
    personnel=personnel,
    projects=projects,
    CRUISE_NUMBER=CRUISE_NUMBER,
    cruise_name=cruise_name,
    cruise_leader=cruise_leader,
    cocruise_leader=cocruise_leader,
    project=project,
    newProject=newProject,
    comment=comment,
    )
