from flask import Blueprint, render_template, request, flash, redirect, url_for
import psycopg2
import psycopg2.extras
import getpass
import uuid
from website.database.get_data import get_data
from website.database.harvest_activities import harvest_activities, get_bottom_depth
from . import DBNAME, CRUISE_NUMBER, METADATA_CATALOGUE, CRUISE_DETAILS_TABLE, VESSEL_NAME, TOKTLOGGER
import requests
import numpy as np
from datetime import datetime as dt

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

    # Need a better solution than harvesting each time visit home. This will be cumbersome on long cruises
    activities_df = harvest_activities(TOKTLOGGER, DBNAME, METADATA_CATALOGUE).reset_index()

    activities_df['message'] = 'Okay'

    # Get this from configuration file
    required_cols = [
    'pi_name',
    'pi_email',
    'pi_institution',
    'stationname',
    'geartype'
    ]

    for col in required_cols:
        activities_df.loc[activities_df[col].isnull(), 'message'] = 'Missing metadata'

    if 'Missing metadata' in activities_df['message'].values:
        missing = True
    else:
        missing = False

    activities_df_home = activities_df[['stationname','eventdate', 'eventtime','decimallatitude','decimallongitude','geartype','pi_name','message','id']]
    activities_df_home.sort_values(by=['eventdate', 'eventtime'], ascending=False, inplace=True)

    num_activities = len(activities_df_home)

    return render_template(
    "home.html",
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
