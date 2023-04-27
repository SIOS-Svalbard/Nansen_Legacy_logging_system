from flask import Blueprint, render_template, request, flash, redirect, url_for
import psycopg2
import psycopg2.extras
import uuid
from website.lib.get_data import get_data, get_cruise
from . import DB
from website.lib.other_functions import combine_personnel_details

registrations = Blueprint('registrations', __name__)

@registrations.route('/register', methods=['GET'])
def register():

    return render_template("register.html")

@registrations.route('/register/cruiseDetails', methods=['GET', 'POST'])
def cruiseDetails():

    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

    df = get_data(DB, 'personnel_'+CRUISE_NUMBER)
    df.sort_values(by='last_name', inplace=True)
    df['personnel'] = df['first_name'] + ' ' + df['last_name'] + ' (' + df['email'] + ')'
    personnel = list(df['personnel'])

    proj_df = get_data(DB, 'projects')
    proj_df.sort_values(by='project', inplace=True)
    projects = list(proj_df['project'])

    if len(cruise_details_df) > 0:
        current_cruise_name = cruise_details_df['cruise_name'].item()
        current_cruise_project = cruise_details_df['project'].item()
        current_cruise_leader =  combine_personnel_details(cruise_details_df['cruise_leader_name'].item(),cruise_details_df['cruise_leader_email'].item())[0]
        current_cocruise_leader = combine_personnel_details(cruise_details_df['co_cruise_leader_name'].item(),cruise_details_df['co_cruise_leader_email'].item())[0]
        current_cruise_comment = cruise_details_df['comment'].item()
    else:
        current_cruise_name = ''
        current_cruise_project = ''
        current_cruise_leader = ''
        current_cocruise_leader = ''
        current_cruise_comment = ''

    if request.method == 'POST':

        cruise_leader = request.form.get('cruiseLeader')
        cruise_leader_name = cruise_leader.split(' (')[0]
        cruise_leader_orcid = df.loc[df['personnel'] == cruise_leader, 'orcid'].iloc[0]
        cruise_leader_email = df.loc[df['personnel'] == cruise_leader, 'email'].iloc[0]
        cruise_leader_institution = df.loc[df['personnel'] == cruise_leader, 'institution'].iloc[0]

        try:
            co_cruise_leader = request.form.get('coCruiseLeader')
            co_cruise_leader_name = co_cruise_leader.split(' (')[0]
            co_cruise_leader_orcid = df.loc[df['personnel'] == co_cruise_leader, 'orcid'].iloc[0]
            co_cruise_leader_email = df.loc[df['personnel'] == co_cruise_leader, 'email'].iloc[0]
            co_cruise_leader_institution = df.loc[df['personnel'] == co_cruise_leader, 'institution'].iloc[0]
        except:
            co_cruise_leader = ''
            co_cruise_leader_name = ''
            co_cruise_leader_orcid = ''
            co_cruise_leader_email = ''
            co_cruise_leader_institution = ''

        project = request.form.get('project').capitalize()
        cruise_name = request.form.get('cruiseName').capitalize()
        comment = request.form.get('comment')

        conn = psycopg2.connect(**DB)
        cur = conn.cursor()

        cur.execute(f'''UPDATE cruises SET
        cruise_name = '{cruise_name}',
        project = '{project}',
        cruise_leader_orcid = '{cruise_leader_orcid}',
        cruise_leader_name = '{cruise_leader_name}',
        cruise_leader_institution = '{cruise_leader_institution}',
        cruise_leader_email = '{cruise_leader_email}',
        co_cruise_leader_orcid = '{co_cruise_leader_orcid}',
        co_cruise_leader_name = '{co_cruise_leader_name}',
        co_cruise_leader_institution = '{co_cruise_leader_institution}',
        co_cruise_leader_email = '{co_cruise_leader_email}',
        comment = '{comment}'
        WHERE cruise_number = '{CRUISE_NUMBER}';
        ''')

        conn.commit()
        cur.close()
        conn.close()

        flash('Cruise details edited!', category='success')

        return redirect(url_for('views.home'))

    return render_template(
    "register/cruiseDetails.html",
    personnel=personnel,
    projects=projects,
    CRUISE_NUMBER=CRUISE_NUMBER,
    current_cruise_name=current_cruise_name,
    current_cruise_leader=current_cruise_leader,
    current_cocruise_leader=current_cocruise_leader,
    current_cruise_project=current_cruise_project,
    current_cruise_comment=current_cruise_comment,
    )

@registrations.route('/register/institutions', methods=['GET', 'POST'])
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

            cur.execute(f"INSERT INTO institutions (id, short_name, full_name, comment, created) VALUES ('{uuid.uuid1()}', '{institutionShort}', '{institutionFull}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Institution registered!', category='success')

            return redirect(url_for('registrations.institutions'))

    return render_template("register/institutions.html", short_names = short_names, full_names = full_names, comments = comments, len = len(full_names))

@registrations.route('/register/sampleTypes', methods=['GET', 'POST'])
def sampleTypes():

    df = get_data(DB, 'sample_types')
    df.sort_values(by='sampletype', inplace=True)
    sample_types = list(df['sampletype'])
    comments = list(df['comment'])

    if request.method == 'POST':

        sample_type = request.form.get('sample_type').capitalize()
        comment = request.form.get('comment')

        if sample_type in sample_types:
            flash('Sample type with same full name already registered', category='error')
        elif len(sample_type) < 3:
            flash('Sample type must be at least 3 characters long', category='error')
        else:
            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            cur.execute(f"INSERT INTO sample_types (id, sampleType, comment, created) VALUES ('{uuid.uuid1()}', '{sample_type}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Sample type registered!', category='success')

            return redirect(url_for('registrations.sampleTypes'))

    return render_template("register/sampleTypes.html", registered_sample_types=sample_types, comments=comments, len=len(sample_types))

@registrations.route('/register/gearTypes', methods=['GET', 'POST'])
def gearTypes():

    df = get_data(DB, 'gear_types')
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

            cur.execute(f"INSERT INTO gear_types (id, gearType, comment, created) VALUES ('{uuid.uuid1()}', '{gear_type}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Gear type registered!', category='success')

            return redirect(url_for('registrations.gearTypes'))

    return render_template("register/gearTypes.html", registered_gear_types=gear_types, comments=comments, len=len(gear_types))

@registrations.route('/register/intendedMethods', methods=['GET', 'POST'])
def intendedMethods():

    df = get_data(DB, 'intended_methods')
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

            cur.execute(f"INSERT INTO intended_methods (id, intendedMethod, comment, created) VALUES ('{uuid.uuid1()}', '{intended_method}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Intended method registered!', category='success')

            return redirect(url_for('registrations.intendedMethods'))

    return render_template("register/intendedMethods.html", registered_intended_methods=intended_methods, comments=comments, len=len(intended_methods))

@registrations.route('/register/stations', methods=['GET', 'POST'])
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

            cur.execute(f"INSERT INTO stations_{CRUISE_NUMBER} (id, stationName, decimalLongitude, decimalLatitude, comment, created) VALUES ('{uuid.uuid1()}', '{stationName}', {decimalLongitude}, {decimalLatitude}, '{comment}', CURRENT_TIMESTAMP);")

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
        first_name = request.form.get('first_name').capitalize()
        last_name = request.form.get('last_name').capitalize()
        email = request.form.get('email')
        orcid = request.form.get('orcid')
        print(orcid, type(orcid), len(orcid))
        institution = request.form.get('institution')
        comment = request.form.get('comment')

        if len(orcid) == 0:
            check_orcid = True
        else:
            if len(orcid) != 37:
                check_orcid = False
            elif orcid.startswith('https://orcid.org'):
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
        elif len(email) < 6:
            flash('Email must be at least 6 characters long', category='error')
        elif institution not in registered_institutions:
            flash('Must select an institution from the list', category='error')
        elif not check_orcid:
            flash('Invalid ordid', category='error')
        else:
            conn = psycopg2.connect(**DB)
            cur = conn.cursor()
            cur.execute(f"INSERT INTO personnel_{CRUISE_NUMBER} (id, first_name, last_name, institution, email, orcid, comment, created) VALUES ('{uuid.uuid1()}', '{first_name}','{last_name}','{institution}','{email}','{orcid}','{comment}', CURRENT_TIMESTAMP);")

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

            cur.execute(f"INSERT INTO sex (id, sex, comment, created) VALUES ('{uuid.uuid1()}', '{sex}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Sex registered!', category='success')

            return redirect(url_for('registrations.sex'))

    return render_template("register/sex.html", sexes=sexes, comments=comments, len=len(sexes))

@registrations.route('/register/kingdoms', methods=['GET', 'POST'])
def kingdoms():

    df = get_data(DB, 'kingdoms')
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

            cur.execute(f"INSERT INTO kingdoms (id, kingdom, comment, created) VALUES ('{uuid.uuid1()}', '{kingdom}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Kingdom registered!', category='success')

            return redirect(url_for('registrations.kingdoms'))

    return render_template("register/kingdoms.html", kingdoms=kingdoms, comments=comments, len=len(kingdoms))

@registrations.route('/register/filters', methods=['GET', 'POST'])
def filters():

    df = get_data(DB, 'filters')
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

            cur.execute(f"INSERT INTO filters (id, filter, comment, created) VALUES ('{uuid.uuid1()}', '{filter}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Filter registered!', category='success')

            return redirect(url_for('registrations.filters'))

    return render_template("register/filters.html", filters=filters, comments=comments, len=len(filters))

@registrations.route('/register/projects', methods=['GET', 'POST'])
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

            cur.execute(f"INSERT INTO projects (id, project, comment, created) VALUES ('{uuid.uuid1()}', '{project}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Project registered!', category='success')

            return redirect(url_for('registrations.registeredprojects'))

    return render_template("register/projects.html", projects=projects, comments=comments, len=len(projects))

@registrations.route('/register/storageTemps', methods=['GET', 'POST'])
def storageTemps():

    df = get_data(DB, 'storage_temperatures')
    df.sort_values(by='storagetemp', inplace=True)
    storageTemps = list(df['storagetemp'])
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

            cur.execute(f"INSERT INTO storage_temperatures (id, storageTemp, comment, created) VALUES ('{uuid.uuid1()}', '{storageTemp}', '{comment}', CURRENT_TIMESTAMP);")

            conn.commit()
            cur.close()
            conn.close()

            flash('Storage temperature registered!', category='success')

            return redirect(url_for('registrations.storageTemps'))

    return render_template("register/storageTemps.html", storageTemps=storageTemps, comments=comments, len=len(storageTemps))
