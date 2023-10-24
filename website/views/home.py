from flask import Blueprint, render_template, request, flash, redirect, url_for
import psycopg2
import psycopg2.extras
import uuid
from website.lib.init_cruise_tables import run as init_cruise_tables
from website.lib.get_data import get_cruise, get_cruises
from website.lib.harvest_activities import harvest_activities
from website.lib.harvest_niskins import harvest_niskins
from website import DB, TOKTLOGGER, BTL_FILES_FOLDER, CONFIG, FIELDS_FILEPATH
from website.lib.get_dict_for_list_of_fields import get_dict_for_list_of_fields
import requests
import pandas as pd
from website.lib.get_missing import get_missing_activities, get_missing_niskins
from website.lib.other_functions import sort_dataframe

home = Blueprint('home', __name__)

@home.route('/', methods=['GET', 'POST'])
def homepage():

    cruise_details_df = get_cruise(DB)

    if isinstance(cruise_details_df, pd.DataFrame):

        CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

        # If the cruise is stated to be in progress (current = True)

        cruise_leader_name = cruise_details_df['cruise_leader_name'].values[-1]
        co_cruise_leader_name = cruise_details_df['co_cruise_leader_name'].values[-1]
        cruise_name = cruise_details_df['cruise_name'].values[-1]

        # Need a better solution than harvesting each time visit home. This could become cumbersome on long cruises
        activities_df = harvest_activities(TOKTLOGGER, DB, CRUISE_NUMBER).reset_index()
        if BTL_FILES_FOLDER and BTL_FILES_FOLDER != '':
            harvest_niskins(DB, CRUISE_NUMBER, BTL_FILES_FOLDER)
        activities_df['message'] = 'Okay'

        missing_activities_df, output_config_dict = get_missing_activities()

        missing = False
        if len(missing_activities_df) > 0:
            missing = True

        niskins_df, output_config_dict = get_missing_niskins()

        if len(niskins_df) > 0:
            missing = True

        activities_df.loc[activities_df['id'].isin(missing_activities_df['id']), 'message'] = 'Missing metadata'

        activities_df = sort_dataframe(activities_df)
        activities_df_home = activities_df[['stationname','eventdate', 'eventtime','decimallatitude','decimallongitude','geartype','pi_name','message','id', 'number_of_children']]

        num_activities = len(activities_df_home)

        if request.method == 'POST':
            form_input = request.form.to_dict(flat=False)

            if request.form['submit'] == 'endCruise':

                conn = psycopg2.connect(**DB)
                cur = conn.cursor()
                exe_str = f"UPDATE cruises SET current = false WHERE cruise_number = '{CRUISE_NUMBER}';"
                cur.execute(exe_str)
                conn.commit()
                cur.close()
                conn.close()
                # UPDATE PSQL TABLE FOR CRUISE, MAKE CURRENT = TRUE
                # If successful, return home_not_during_cruise
                return redirect('/')

        return render_template(
        "home_during_cruise.html",
        CRUISE_NUMBER=CRUISE_NUMBER,
        cruise_leader_name=cruise_leader_name,
        co_cruise_leader_name=co_cruise_leader_name,
        cruise_name=cruise_name,
        row_data=list(activities_df_home.values.tolist()),
        link_column='id',
        column_names=activities_df_home.columns.values,
        zip=zip,
        num_activities=num_activities,
        TOKTLOGGER=TOKTLOGGER,
        missing=missing
        )

    else:
        # If cruise not currently in progress (all rows current = false)

        try:
            # Pull potential cruise number from TOKTLOGGER
            url = "http://"+TOKTLOGGER+"/api/cruises/current?format=json"
            response = requests.get(url)
            json_cruise = response.json()
            cruise_number_toktlogger = json_cruise['cruiseNumber']
            vessel_name_toktlogger = json_cruise['vesselName']
            toktlogger_on = True
        except:
            toktlogger_on = False
            cruise_number_toktlogger = ''
            vessel_name_toktlogger = ''

        # Pull list of existing cruises for resume_cruise drop-down list
        existing_cruise_numbers = get_cruises(DB)

        if request.method == 'POST':

            form_input = request.form.to_dict(flat=False)

            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            if request.form['submit'] == 'startCruise':
                # If user wants to start the cruise and has hit the 'start cruise' button
                # Retrieve info related to cruise (cruise number, cruise name, vessel name)

                CRUISE_NUMBER = form_input['cruiseNumber'][0]
                VESSEL_NAME = form_input['vesselName'][0]

                if CRUISE_NUMBER in existing_cruise_numbers:
                    cur.close()
                    conn.close()
                    flash('Cruise with this cruise number already exists. Please select a new cruise number or resume the cruise.', category='error')
                else:
                    id = str(uuid.uuid4())
                    cur.execute(f"INSERT INTO cruises (id, cruise_number, vessel_name, current, created) VALUES ('{id}','{CRUISE_NUMBER}','{VESSEL_NAME}',true,CURRENT_TIMESTAMP);")
                    conn.commit()
                    cur.close()
                    conn.close()

                    metadata_columns_list = CONFIG["metadata_catalogue"]["fields_to_use_as_columns"]
                    metadata_columns_dict = get_dict_for_list_of_fields(metadata_columns_list, FIELDS_FILEPATH)

                    init_cruise_tables(DB, CRUISE_NUMBER, metadata_columns_dict)

                    # redirect to home, run the script again now that new cruise is logged with current = true
                    return redirect('/setupCruise/uploadPersonnel')


                # If successful, return home_during_cruise
            elif request.form['submit'] == 'resumeCruise':
                # If user wants to resume cruise and has hit the 'resume cruise' button
                CRUISE_NUMBER = form_input['resumeCruise'][0]
                # UPDATE PSQL TABLE FOR CRUISE, MAKE CURRENT = TRUE
                if CRUISE_NUMBER != '':

                    exe_str = f"UPDATE cruises SET current = true WHERE cruise_number = '{CRUISE_NUMBER}';"
                    cur.execute(exe_str)
                    conn.commit()
                    cur.close()
                    conn.close()
                    # If successful, return home_during_cruise
                    return redirect('/')

                else:

                    flash('Please select a cruise number from the drop-down list', category='warning')

        return render_template(
        "home_not_during_cruise.html",
        cruise_number_toktlogger = cruise_number_toktlogger,
        vessel_name_toktlogger = vessel_name_toktlogger,
        existing_cruise_numbers = existing_cruise_numbers,
        toktlogger_on = toktlogger_on,
        len=len
        )
