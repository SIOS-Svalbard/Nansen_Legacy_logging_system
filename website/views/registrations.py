from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
import psycopg2
import psycopg2.extras
import uuid
from website.lib.get_data import get_data, get_cruise, get_cruise_details, get_personnel_list, get_projects_list
from website import DB
from website.lib.create_template_for_registering_personnel import create_personnel_template
from website.lib.register_personnel_from_file import register_personnel_from_file
from website.lib.other_functions import split_personnel_list

registrations = Blueprint('registrations', __name__)

@registrations.route('/register', methods=['GET'])
def register():

    return render_template("register.html")

@registrations.route('/register/cruiseDetails', methods=['GET', 'POST'])
def cruiseDetails():

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
    "register/cruiseDetails.html",
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

@registrations.route('/register/institution', methods=['GET', 'POST'])
def institutions():

    df = get_data(DB, 'institutions')
    df.sort_values(by='full_name', inplace=True)
    short_names = list(df['short_name'])
    full_names = list(df['full_name'])
    comments = list(df['comment'])

    if request.method == 'POST':

        institutionFull = request.form.get('institutionFull').capitalize()
        institutionShort = request.form.get('institutionShort').capitalize()
        comment = request.form.get('comment')

        if institutionFull in full_names:
            flash('Institution with same full name already registered', category='error')
        elif institutionShort in short_names and institutionShort > 0:
            flash('Institution with same full name already registered', category='error')
        elif len(institutionFull) < 11:
            flash('Institution full name must be longer than 10 characters', category='error')
        elif len(institutionShort) > 10:
            flash('Institution short name must be shorter than 10 characters', category='error')
        else:
            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            cur.execute(f"INSERT INTO institutions (id, short_name, full_name, comment, created) VALUES ('{uuid.uuid4()}', '{institutionShort}', '{institutionFull}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Institution registered!', category='success')

            return redirect(url_for('registrations.institutions'))

    return render_template("register/institutions.html", short_names = short_names, full_names = full_names, comments = comments, len = len(full_names))

@registrations.route('/register/sampleType', methods=['GET', 'POST'])
def sampleTypes():

    df = get_data(DB, 'sampletype')
    df.sort_values(by='sampletype', inplace=True)
    sample_types = list(df['sampletype'])
    subconfigs = list(df['subconfig'])
    comments = list(df['comment'])

    if request.method == 'POST':

        sample_type = request.form.get('sample_type').capitalize()
        subconfig = request.form.get('subconfig').capitalize()
        comment = request.form.get('comment')

        if sample_type in sample_types:
            flash('Sample type with same full name already registered', category='error')
        elif len(sample_type) < 3:
            flash('Sample type must be at least 3 characters long', category='error')
        else:
            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            cur.execute(f"INSERT INTO sampletype (id, sampleType, subconfig, comment, created) VALUES ('{uuid.uuid4()}', '{sample_type}', '{subconfig}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Sample type registered!', category='success')

            return redirect(url_for('registrations.sampleTypes'))

    return render_template("register/sampleTypes.html", registered_sample_types=sample_types, registered_subconfigs=subconfigs, subconfigs=list(set(subconfigs)), comments=comments, len=len(sample_types))

@registrations.route('/register/gearType', methods=['GET', 'POST'])
def gearTypes():

    df = get_data(DB, 'geartype')
    df.sort_values(by='geartype', inplace=True)
    gear_types = list(df['geartype'])
    comments = list(df['comment'])

    if request.method == 'POST':

        gear_type = request.form.get('gear_type').capitalize()
        comment = request.form.get('comment')

        if gear_type in gear_types:
            flash('Gear type with same full name already registered', category='error')
        elif len(gear_type) < 3:
            flash('Gear type must be at least 3 characters long', category='error')
        else:
            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            cur.execute(f"INSERT INTO geartype (id, gearType, comment, created) VALUES ('{uuid.uuid4()}', '{gear_type}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Gear type registered!', category='success')

            return redirect(url_for('registrations.gearTypes'))

    return render_template("register/gearTypes.html", registered_gear_types=gear_types, comments=comments, len=len(gear_types))

@registrations.route('/register/intendedMethod', methods=['GET', 'POST'])
def intendedMethods():

    df = get_data(DB, 'intendedmethod')
    df.sort_values(by='intendedmethod', inplace=True)
    intended_methods = list(df['intendedmethod'])
    comments = list(df['comment'])

    if request.method == 'POST':

        intended_method = request.form.get('intended_method')
        comment = request.form.get('comment')

        if intended_method in intended_methods:
            flash('Intended method with same full name already registered', category='error')
        elif len(intended_method) < 3:
            flash('Intended method must be at least 3 characters long', category='error')
        else:
            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            cur.execute(f"INSERT INTO intendedmethod (id, intendedMethod, comment, created) VALUES ('{uuid.uuid4()}', '{intended_method}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Intended method registered!', category='success')

            return redirect(url_for('registrations.intendedMethods'))

    return render_template("register/intendedMethods.html", registered_intended_methods=intended_methods, comments=comments, len=len(intended_methods))

@registrations.route('/register/stationName', methods=['GET', 'POST'])
def stations():

    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

    df = get_data(DB, 'stations_'+CRUISE_NUMBER)
    df.sort_values(by='stationname', inplace=True)
    stationNames = list(df['stationname'])
    decimalLatitudes = list(df['decimallatitude'])
    decimalLongitudes = list(df['decimallongitude'])
    comments = list(df['comment'])

    if request.method == 'POST':

        stationName = request.form.get('stationName').capitalize()
        decimalLatitude = float(request.form.get('decimalLatitude'))
        decimalLongitude = float(request.form.get('decimalLongitude'))
        comment = request.form.get('comment')

        # Add optional validation based on distance to another station.

        if stationName in stationNames:
            flash('Station with same name already registered', category='error')
        elif len(stationName) < 2:
            flash('Station name must be at least 2 characters long', category='error')
        elif decimalLatitude > 90:
            flash('Latitude must be a between -90 and 90', category='error')
        elif decimalLatitude < -90:
            flash('Latitude must be a between -90 and 90', category='error')
        elif decimalLongitude > 180:
            flash('Longitude must be a between -180 and 180', category='error')
        elif decimalLongitude < -180:
            flash('Longitude must be a between -180 and 180', category='error')
        else:
            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            cur.execute(f"INSERT INTO stations_{CRUISE_NUMBER} (id, stationName, decimalLongitude, decimalLatitude, comment, created) VALUES ('{uuid.uuid4()}', '{stationName}', {decimalLongitude}, {decimalLatitude}, '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Station registered!', category='success')

            return redirect(url_for('registrations.stations'))

    return render_template("register/stations.html", registered_stations=stationNames, decimalLatitudes = decimalLatitudes, decimalLongitudes = decimalLongitudes, comments=comments, len=len(stationNames))

@registrations.route('/register/personnel', methods=['GET', 'POST'])
def personnel():

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

    df = get_data(DB, 'institutions')
    registered_institutions = list(df['full_name'])

    if request.method == 'POST':
        form_input = request.form.to_dict(flat=False)

        if 'submit' in form_input.keys() and form_input['submit'] == ['generateExcel']:
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
                return redirect(url_for('registrations.personnel'))

        else:
            first_name = request.form.get('first_name').capitalize()
            last_name = request.form.get('last_name').capitalize()
            email = request.form.get('email')
            orcid = request.form.get('orcid')
            institution = request.form.get('institution')
            comment = request.form.get('comment')

            if len(orcid) == 0:
                check_orcid = True
            else:
                if len(orcid) != 37:
                    check_orcid = False
                elif orcid.startswith('https://orcid.org/'):
                    check_orcid = True
                else:
                    check_orcid = False

            if len(first_name) < 2:
                flash('First name must be at least 2 characters long', category='error')
            elif len(last_name) < 2:
                flash('Last name must be at least 2 characters long', category='error')
            elif len(first_name) > 30:
                flash('First name cannot be longer than 30 characters long', category='error')
            elif len(last_name) > 30:
                flash('Last name cannot be longer than 30 characters long', category='error')
            elif '@' not in email:
                flash('Email must include an @ symbol', category='error')
            elif email in emails:
                flash(f'Person with email {email} already registered', category='error')
            elif len(email) < 6:
                flash('Email must be at least 6 characters long', category='error')
            elif institution not in registered_institutions:
                flash('Must select an institution from the list', category='error')
            elif not check_orcid:
                flash('Invalid ordid', category='error')
            else:
                personnel = f"{first_name} {last_name} ({email})"
                conn = psycopg2.connect(**DB)
                cur = conn.cursor()
                cur.execute(f"INSERT INTO personnel_{CRUISE_NUMBER} (id, personnel, first_name, last_name, institution, email, orcid, comment, created) VALUES ('{uuid.uuid4()}', '{personnel}', '{first_name}','{last_name}','{institution}','{email}','{orcid}','{comment}', CURRENT_TIMESTAMP);")

                conn.commit()
                cur.close()
                conn.close()

                flash('Person registered!', category='success')

                return redirect(url_for('registrations.personnel'))

    return render_template("register/personnel.html", registered_institutions=registered_institutions, first_names=first_names, last_names = last_names, emails = emails, institutions = institutions, orcids=orcids, comments=comments, len=len(first_names))

@registrations.route('/register/sex', methods=['GET', 'POST'])
def sex():

    df = get_data(DB, 'sex')
    #df.sort_values(by='sex', inplace=True)
    sexes = list(df['sex'])
    comments = list(df['comment'])

    if request.method == 'POST':

        sex = request.form.get('sex')
        comment = request.form.get('comment')

        if sex in sexes:
            flash('Sex with same full name already registered', category='error')
        elif len(sex) < 1:
            flash('Sex must be at least 1 character long', category='error')
        else:
            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            cur.execute(f"INSERT INTO sex (id, sex, comment, created) VALUES ('{uuid.uuid4()}', '{sex}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Sex registered!', category='success')

            return redirect(url_for('registrations.sex'))

    return render_template("register/sex.html", sexes=sexes, comments=comments, len=len(sexes))

@registrations.route('/register/kingdom', methods=['GET', 'POST'])
def kingdoms():

    df = get_data(DB, 'kingdom')
    df.sort_values(by='kingdom', inplace=True)
    kingdoms = list(df['kingdom'])
    comments = list(df['comment'])

    if request.method == 'POST':

        kingdom = request.form.get('kingdom').capitalize()
        comment = request.form.get('comment')

        if kingdom in kingdoms:
            flash('Kingdom with same full name already registered', category='error')
        elif len(kingdom) < 3:
            flash('Kingdom name must be at least 3 characters long', category='error')
        else:
            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            cur.execute(f"INSERT INTO kingdom (id, kingdom, comment, created) VALUES ('{uuid.uuid4()}', '{kingdom}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Kingdom registered!', category='success')

            return redirect(url_for('registrations.kingdoms'))

    return render_template("register/kingdoms.html", kingdoms=kingdoms, comments=comments, len=len(kingdoms))

@registrations.route('/register/filter', methods=['GET', 'POST'])
def filters():

    df = get_data(DB, 'filter')
    df.sort_values(by='filter', inplace=True)
    filters = list(df['filter'])
    comments = list(df['comment'])

    if request.method == 'POST':

        filter = request.form.get('filter')
        comment = request.form.get('comment')

        if filter in filters:
            flash('Filter with same full name already registered', category='error')
        elif len(filter) < 2:
            flash('Filter name must be at least 2 characters long', category='error')
        else:
            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            cur.execute(f"INSERT INTO filter (id, filter, comment, created) VALUES ('{uuid.uuid4()}', '{filter}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Filter registered!', category='success')

            return redirect(url_for('registrations.filters'))

    return render_template("register/filters.html", filters=filters, comments=comments, len=len(filters))

@registrations.route('/register/project', methods=['GET', 'POST'])
def registeredprojects():

    df = get_data(DB, 'projects')
    df.sort_values(by='project', inplace=True)
    projects = list(df['project'])
    comments = list(df['comment'])

    if request.method == 'POST':

        project = request.form.get('project').capitalize()
        comment = request.form.get('comment')

        if project in projects:
            flash('Project with same full name already registered', category='error')
        elif len(project) < 7:
            flash('Project name must be at least 7 characters long', category='error')
        else:
            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            cur.execute(f"INSERT INTO projects (id, project, comment, created) VALUES ('{uuid.uuid4()}', '{project}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Project registered!', category='success')

            return redirect(url_for('registrations.registeredprojects'))

    return render_template("register/projects.html", projects=projects, comments=comments, len=len(projects))

@registrations.route('/register/storageTemp', methods=['GET', 'POST'])
def storageTemps():

    df = get_data(DB, 'storagetemperature')
    df.sort_values(by='storagetemperature', inplace=True)
    storageTemps = list(df['storagetemperature'])
    comments = list(df['comment'])

    if request.method == 'POST':

        storageTemp = request.form.get('storageTemp')
        comment = request.form.get('comment')

        if storageTemp in storageTemps:
            flash('Project with same full name already registered', category='error')
        elif len(storageTemp) < 1:
            flash('Storage temperature must be at least 1 character long', category='error')
        else:
            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            cur.execute(f"INSERT INTO storagetemperature (id, storageTemp, comment, created) VALUES ('{uuid.uuid4()}', '{storageTemp}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Storage temperature registered!', category='success')

            return redirect(url_for('registrations.storageTemps'))

    return render_template("register/storageTemps.html", storageTemps=storageTemps, comments=comments, len=len(storageTemps))
