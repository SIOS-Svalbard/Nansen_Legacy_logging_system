from flask import Blueprint, render_template, request, flash, redirect, url_for
import psycopg2
import psycopg2.extras
import getpass
import uuid
from website.database.get_data import get_data
from website.database.harvest_activities import harvest_activities, get_bottom_depth
from website.other_functions.calculations import distanceCoordinates
from . import DBNAME, CRUISE_NUMBER, METADATA_CATALOGUE, CRUISE_DETAILS_TABLE, VESSEL_NAME, TOKTLOGGER
import requests
import numpy as np
from datetime import datetime as dt
#from string import Template

views = Blueprint('views', __name__)

@views.route('/', methods=['GET'])
def home():

    cruise_details_df = get_data(DBNAME, CRUISE_DETAILS_TABLE)
    if len(cruise_details_df) > 0:
        cruise_leader_name = cruise_details_df['cruise_leader_name'].values[-1]
        co_cruise_leader_name = cruise_details_df['co_cruise_leader_name'].values[-1]
        cruise_name = cruise_details_df['cruise_name'].values[-1]
    else:
        cruise_leader_name = co_cruise_leader_name = cruise_name = False

    activities_df = harvest_activities(TOKTLOGGER, DBNAME, METADATA_CATALOGUE, CRUISE_NUMBER, VESSEL_NAME).reset_index()

    activities_df['message'] = 'Okay'

    required_cols = [
    'pi_name',
    'pi_email',
    'pi_institution',
    'stationname',
    'geartype'
    ]

    for col in required_cols:
        activities_df.loc[activities_df[col].isnull(), 'message'] = 'Missing metadata'

    activities_df_home = activities_df[['stationname','eventdate', 'enddate','decimallatitude','decimallongitude','geartype','pi_name','message','id']]
    activities_df_home.sort_values(by=['eventdate'], ascending=False, inplace=True)

    num_activities = len(activities_df_home)

    return render_template("home.html", CRUISE_NUMBER=CRUISE_NUMBER, cruise_leader_name=cruise_leader_name, co_cruise_leader_name=co_cruise_leader_name, cruise_name=cruise_name, row_data=list(activities_df_home.values.tolist()), link_column='id', column_names=activities_df_home.columns.values, zip=zip, num_activities=num_activities, TOKTLOGGER=TOKTLOGGER)

@views.route('/editActivity/<eventID>', methods=['GET', 'POST'])
def edit_activity_page(eventID):

    df_personnel = get_data(DBNAME, 'personnel')
    df_personnel.sort_values(by='last_name', inplace=True)
    df_personnel['personnel'] = df_personnel['first_name'] + ' ' + df_personnel['last_name'] + ' (' + df_personnel['email'] + ')'
    personnel = list(df_personnel['personnel'])

    df_gears = get_data(DBNAME, 'gear_types')
    df_gears.sort_values(by='geartype', inplace=True)
    gearTypes = list(df_gears['geartype'])

    df_stations = get_data(DBNAME, 'stations')
    df_stations.sort_values(by='stationname', inplace=True)
    stationNames = list(df_stations['stationname'])

    df_metadata_catalogue = get_data(DBNAME, METADATA_CATALOGUE)

    if eventID == 'addNew':
        decimalLatitude = None
        decimalLongitude = None
        stationName = ''
        gearType = ''
        catalogNumber = ''
        endDecimalLatitude = None
        endDecimalLongitude = None
        eventDate = None
        eventTime = None
        endDate = None
        endTime = None
        minimumDepthInMeters = None
        maximumDepthInMeters = None
        comments1 = ''
        pi_name = None
        pi_email = None
        samplingProtocolDoc = ''
        samplingProtocolSection = ''
        samplingProtocolVersion = ''
        recordedBy_name = None
        recordedBy_email = None
    else:
        decimalLatitude = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'decimallatitude'].iloc[0]
        decimalLongitude = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'decimallongitude'].iloc[0]
        stationName = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'stationname'].iloc[0]
        gearType = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'geartype'].iloc[0]
        catalogNumber = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'catalognumber'].iloc[0]
        endDecimalLatitude = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'enddecimallatitude'].iloc[0]
        endDecimalLongitude = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'enddecimallongitude'].iloc[0]
        eventDate = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'eventdate'].iloc[0]
        eventTime = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'eventtime'].iloc[0]
        endDate = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'enddate'].iloc[0]
        endTime = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'endtime'].iloc[0]
        minimumDepthInMeters = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'minimumdepthinmeters'].iloc[0]
        maximumDepthInMeters = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'maximumdepthinmeters'].iloc[0]
        comments1 = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'comments1'].iloc[0]
        pi_name = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'pi_name'].iloc[0]
        pi_email = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'pi_email'].iloc[0]
        samplingProtocolDoc = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'samplingprotocoldoc'].iloc[0]
        samplingProtocolSection = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'samplingprotocolsection'].iloc[0]
        samplingProtocolVersion = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'samplingprotocolversion'].iloc[0]
        recordedBy_name = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'recordedby_name'].iloc[0]
        recordedBy_email = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'recordedby_email'].iloc[0]
        #minimumElevationInMeters =
        #maximumElevationInMeters =

    if pi_name is not None:
        pi_names = pi_name.split(' | ')
        pi_emails = pi_email.split(' | ')
        pis = [f"{name} ({email})" for (name, email) in zip(pi_names, pi_emails)]
    else:
        pis = []

    if recordedBy_name is not None:
        recordedBy_names = recordedBy_name.split(' | ')
        recordedBy_emails = recordedBy_email.split(' | ')
        recordedBys = [f"{name} ({email})" for (name, email) in zip(recordedBy_names, recordedBy_emails)]
    else:
        recordedBys = []

    if request.method == 'POST':
        new_uuid = request.form.get('uuid')
        catalogNumber = request.form.get('catalogNumber')
        stationName = request.form.get('stationName')
        gearType = request.form.get('gearType')
        decimalLatitude = request.form.get('decimalLatitude')
        decimalLongitude = request.form.get('decimalLongitude')
        endDecimalLatitude = request.form.get('endDecimalLatitude')
        endDecimalLongitude = request.form.get('endDecimalLongitude')
        eventDate = request.form.get('eventDate')
        eventTime = request.form.get('eventTime')
        endDate = request.form.get('endDate')
        endTime = request.form.get('endTime')
        minDepthInMeters = request.form.get('minDepthInMeters')
        maxDepthInMeters = request.form.get('maxDepthInMeters')
        minElevationInMeters = request.form.get('minElevationInMeters')
        maxElevationInMeters = request.form.get('maxElevationInMeters')
        pis = request.form.getlist('pis')
        recordedBys = request.form.getlist('recordedBys')
        samplingProtocolDoc = request.form.get('samplingProtocolDoc')
        samplingProtocolSection = request.form.get('samplingProtocolSection')
        samplingProtocolVersion = request.form.get('samplingProtocolVersion')
        comment = request.form.get('comment')

        print(samplingProtocolDoc)

        startDateTime = dt.strptime(eventDate + eventTime, '%Y-%m-%d%H:%M:%S')

        print(startDateTime)
        if new_uuid != '':
            new_uuid = new_uuid.replace('+','-').replace('/','-')
            try:
                uuid.UUID(new_uuid)
            except:
                new_uuid = False
        else:
            new_uuid = str(uuid.uuid1())

        if endDate != '' and endTime != '':
            endDateTime = dt.strptime(endDate + endTime, '%Y-%m-%d%H:%M:%S')
        else:
            # Assigning a dummy datetime in the future for the below validations to work.
            endDateTime = dt(3000,1,1)

        if new_uuid == False:
            flash('Invalid UUID. Enter a valid UUID or remove and one will be assigned automatically', category='error')
        elif new_uuid in df_metadata_catalogue['id'].astype(str).values and new_uuid != eventID:
            flash('Univerisally unique ID already registered. Please use a different one.', category='error')
        elif stationName == '':
            flash('Please select a station name from the drop-down list', category='error')
        elif gearType == '':
            flash('Please select a gear type from the drop-down list', category='error')
        elif 'Choose...' in pis and len(pis) == 1:
            flash('Please select at least one person as PI from the drop-down list', category='error')
        elif 'Choose...' in recordedBys and len(recordedBys) == 1:
            flash('Please select at least one person who was involved in recording this activity from the drop-down list', category='error')
        elif endDate == '' and endTime != '':
            flash('Please select an end time or remove the end date. Both or none are required.', category='error')
        elif endDate != '' and endTime == '':
            flash('Please select an end date or remove the end time. Both or none are required.', category='error')
        elif endDateTime <= startDateTime:
            flash('End date and time must be after the start date and time', category='error')
        elif startDateTime >= dt.utcnow():
            flash('Start date and time must be in the past', category='error')
        elif endDateTime >= dt.utcnow() and endDateTime != dt(3000,1,1):
            flash('End date and time must be in the past', category='error')
        elif minDepthInMeters > maxDepthInMeters:
            flash('Maximum depth must be greater than minimum depth', category='error')
        elif minElevationInMeters > maxElevationInMeters:
            flash('Maximum elevation must be greater than minimum elevation', category='error')
        elif 'Choose...' in pis and len(pis) == 1:
            flash('Please select at least one person as PI from the drop-down list', category='error')
        elif 'Choose...' in recordedBys and len(recordedBys) == 1:
            flash('Please select at least one person who was involved in recording this activity from the drop-down list', category='error')
        else:

            if endDateTime == dt(3000,1,1):
                endDateTime = 'NULL'
                endDate = 'NULL'
                endTime = 'NULL'
            else:
                endDateTime = f"'{endDateTime}'"
                endDate = f"'{endDate}'"
                endTime = f"'{endTime}'"

            pi_names_list = []
            pi_emails_list = []
            pi_institutions_list = []

            for pi in pis:
                if pi != 'Choose...':
                    pi_first_name = df_personnel.loc[df_personnel['personnel'] == pi, 'first_name'].item()
                    pi_last_name = df_personnel.loc[df_personnel['personnel'] == pi, 'last_name'].item()
                    pi_name = pi_first_name + ' ' + pi_last_name
                    pi_email = df_personnel.loc[df_personnel['personnel'] == pi, 'email'].item()
                    pi_institution = df_personnel.loc[df_personnel['personnel'] == pi, 'institution'].item()

                    pi_names_list.append(pi_name)
                    pi_emails_list.append(pi_email)
                    pi_institutions_list.append(pi_institution)

            pi_names = " | ".join(pi_names_list)
            pi_emails = " | ".join(pi_emails_list)
            pi_institutions = " | ".join(pi_institutions_list)

            recordedBy_names_list = []
            recordedBy_emails_list = []
            recordedBy_institutions_list = []

            for recordedBy in recordedBys:
                if recordedBy != 'Choose...':
                    recordedBy_first_name = df_personnel.loc[df_personnel['personnel'] == recordedBy, 'first_name'].item()
                    recordedBy_last_name = df_personnel.loc[df_personnel['personnel'] == recordedBy, 'last_name'].item()
                    recordedBy_name = recordedBy_first_name + ' ' + recordedBy_last_name
                    recordedBy_email = df_personnel.loc[df_personnel['personnel'] == recordedBy, 'email'].item()
                    recordedBy_institution = df_personnel.loc[df_personnel['personnel'] == recordedBy, 'institution'].item()

                    recordedBy_names_list.append(recordedBy_name)
                    recordedBy_emails_list.append(recordedBy_email)
                    recordedBy_institutions_list.append(recordedBy_institution)

            recordedBy_names = " | ".join(recordedBy_names_list)
            recordedBy_emails = " | ".join(recordedBy_emails_list)
            recordedBy_institutions = " | ".join(recordedBy_institutions_list)

            # bottomdepthinmeters = get_bottom_depth(startDateTime, TOKTLOGGER) # Can't trust manually assigned time or coordinates so can't reliably harvest bottom depth

            if endDecimalLatitude == '':
                endDecimalLatitude = 'NULL'
            if endDecimalLongitude == '':
                endDecimalLongitude = 'NULL'
            if minElevationInMeters == '':
                minElevationInMeters = 'NULL'
            if maxElevationInMeters == '':
                maxElevationInMeters = 'NULL'
            if minDepthInMeters == '':
                minDepthInMeters = 'NULL'
            if maxDepthInMeters == '':
                maxDepthInMeters = 'NULL'
            #if comment == None:
            #    comment = ''

            conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
            cur = conn.cursor()

            if eventID == 'addNew':

                created = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                modified = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                history = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record created manually from add activity page")
                source = "Add activity page"

                exe_str = f'''INSERT INTO {METADATA_CATALOGUE}
                (id,
                catalognumber,
                cruisenumber,
                vesselname,
                stationname,
                eventdate,
                eventtime,
                enddate,
                endtime,
                decimallatitude,
                decimallongitude,
                enddecimallatitude,
                enddecimallongitude,
                minimumdepthinmeters,
                maximumdepthinmeters,
                pi_name,
                pi_email,
                pi_institution,
                recordedby_name,
                recordedby_email,
                recordedby_institution,
                comments1,
                geartype,
                samplingprotocoldoc,
                samplingprotocolsection,
                samplingprotocolversion,
                created,
                modified,
                history,
                source,
                other)
                VALUES
                ('{new_uuid}',
                '{catalogNumber}',
                {CRUISE_NUMBER},
                '{VESSEL_NAME}',
                '{stationName}',
                '{eventDate}',
                '{eventTime}',
                {endDate},
                {endTime},
                {decimalLatitude},
                {decimalLongitude},
                {endDecimalLatitude},
                {endDecimalLongitude},
                {minDepthInMeters},
                {maxDepthInMeters},
                '{pi_name}',
                '{pi_email}',
                '{pi_institution}',
                '{recordedBy_names}',
                '{recordedBy_emails}',
                '{recordedBy_institutions}',
                '{comment}',
                '{gearType}',
                '{samplingProtocolDoc}',
                '{samplingProtocolSection}',
                '{samplingProtocolVersion}',
                '{created}',
                '{modified}',
                '{history}',
                '{source}',
                '"minimumElevationInMeters" => "{minElevationInMeters}",
                "maximumElevationInMeters" => "{maxElevationInMeters}",'
                );'''

                cur.execute(exe_str)

                conn.commit()
                cur.close()
                conn.close()

                flash('Activity registered!', category='success')

            else:

                history = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'history'].iloc[0]
                history = history + '\n' + dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record modified using edit activity page")
                modified = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

                exe_str = f'''UPDATE {METADATA_CATALOGUE} SET
                id = '{new_uuid}',
                catalognumber = '{catalogNumber}',
                stationname = '{stationName}',
                eventdate = '{eventDate}',
                eventtime = '{eventTime}',
                enddate = {endDate},
                endtime = {endTime},
                decimallatitude = {decimalLatitude},
                decimallongitude = {decimalLongitude},
                enddecimallatitude = {endDecimalLatitude},
                enddecimallongitude = {endDecimalLongitude},
                minimumdepthinmeters = {minDepthInMeters},
                maximumdepthinmeters = {maxDepthInMeters},
                pi_name = '{pi_name}',
                pi_email = '{pi_email}',
                pi_institution = '{pi_institution}',
                recordedby_name = '{recordedBy_names}',
                recordedby_email = '{recordedBy_emails}',
                recordedby_institution = '{recordedBy_institutions}',
                comments1 = '{comment}',
                geartype = '{gearType}',
                samplingprotocoldoc = '{samplingProtocolDoc}',
                samplingprotocolsection = '{samplingProtocolSection}',
                samplingprotocolversion = '{samplingProtocolVersion}',
                modified = '{modified}',
                history = '{history}'
                WHERE id = '{eventID}';'''

                cur.execute(exe_str)

                conn.commit()
                cur.close()
                conn.close()

                flash('Activity edited!', category='success')

            return redirect(url_for('views.home'))

    if eventID == 'addNew':
        eventID = ''

    return render_template(
    "addActivity.html",
    personnel=personnel,
    gearTypes=gearTypes,
    stationNames=stationNames,
    decimalLatitude=decimalLatitude,
    decimalLongitude=decimalLongitude,
    stationName=stationName,
    gearType=gearType,
    catalogNumber=catalogNumber,
    eventID=eventID,
    endDecimalLatitude=endDecimalLatitude,
    endDecimalLongitude=endDecimalLongitude,
    eventDate=eventDate,
    eventTime=eventTime,
    endDate=endDate,
    endTime=endTime,
    minimumDepthInMeters=minimumDepthInMeters,
    maximumDepthInMeters=maximumDepthInMeters,
    #minimumElevationInMeters=minimumElevationInMeters,
    #maximumElevationInMeters=maximumElevationInMeters,
    pis=pis,
    recordedBys=recordedBys,
    samplingProtocolDoc=samplingProtocolDoc,
    samplingProtocolVersion=samplingProtocolVersion,
    samplingProtocolSection=samplingProtocolSection,
    comments1=comments1
    )
