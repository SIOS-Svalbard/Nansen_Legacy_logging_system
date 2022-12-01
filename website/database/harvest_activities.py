#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 13:34:15 2022
Based on https://github.com/SIOS-Svalbard/darwinsheet/blob/master/scripts/toktlogger_json_to_df.py

@author: lukem
"""

import pandas as pd
import datetime
from datetime import datetime as dt
import numpy as np
import requests
import psycopg2
import getpass
from website.database.get_data import get_data, get_registered_activities

def round_4dp(num):
    '''
    Round a number to 4 decimal places

    Parameters
    ----------
    num : float
        Number to round

    Returns
    -------
    rounded_num : float
        Number rounded to 4dp

    '''

    rounded_num = int(num * 10000 + 0.5) / 10000

    return rounded_num

def flattenjson( b, delim ):
    '''

    Parameters
    ----------
    b : TYPE: dict
        DESCRIPTION: json dictionary
    delim : TYPE: string
        DESCRIPTION: When dictionary is flattened, child key is appended to the parent key separated by this delimiter.

    Returns
    -------
    val : TYPE: dict
        DESCRIPTION: dictionary with one tier flattened (put on same level as parent)

    '''
    val = {}
    for i in b.keys():
        if isinstance( b[i], dict ):
            get = flattenjson( b[i], delim )
            for j in get.keys():
                val[ i + delim + j ] = get[j]
        else:
            val[i] = b[i]

    return val

def get_bottom_depth(start_datetime, TOKTLOGGER):
    '''
    Get seabed depth below vessel at a certain time

    start_datetime: type datetime object
                    time for which you want to retrieve the bottom depth
    TOKTLOGGER: type string
                IP or DNS of the Toktlogger
    '''
    start_date = start_datetime.strftime('%Y-%m-%d')
    start_hh = "{:02d}".format(start_datetime.hour)
    start_mm = "{:02d}".format(start_datetime.minute)
    start_ss = start_datetime.strftime('%S.%f')[:-3]
    start_datetime_p2 = start_datetime + datetime.timedelta(seconds=2)
    end_date = start_datetime_p2.strftime('%Y-%m-%d')
    ethh = "{:02d}".format(start_datetime_p2.hour)
    etmm = "{:02d}".format(start_datetime_p2.minute)
    etss = start_datetime_p2.strftime('%S.%f')[:-3]
    url = "http://"+TOKTLOGGER+"/api/instrumentData/inPeriod?after="+start_date+"T"+start_hh+"%3A"+start_mm+"%3A"+start_ss+"Z&before="+end_date+"T"+ethh+"%3A"+etmm+"%3A"+etss+"Z&mappingIds=depth&format=json"
    response = requests.get(url)
    json_bd = response.json()

    if len(json_bd) >= 1:
        bd = []
        for i, t in enumerate(json_bd):
            bd.append(t['numericValue'])
        bottomdepthinmeters = np.median([bd])
    else:
        bottomdepthinmeters = 'NULL'

    return bottomdepthinmeters

def harvest_activities(TOKTLOGGER, DB, CRUISE_NUMBER):
    '''
    Provide IP or DNS of toktlogger to access IMR API

    Returns single dataframe that includes details of all the activities
    '''

    # Pull data from IMR API in json format. URL should match IMR API host.

    if TOKTLOGGER != False:
        try:
            url = "http://"+TOKTLOGGER+"/api/activities/inCurrentCruise?format=json"
            response = requests.get(url)
            json_activities = response.json()
        except:
            print("\nCould not connect to the Toktlogger\n")
            json_activities = []
    else:
        json_activities = []

    registered_activities = get_registered_activities(DB, CRUISE_NUMBER)['id'].values

    to_remove = [] # indexes of activities that are already registered don't need to be registered again. Creating a list of those, removing after for loop.

    for idx, val in enumerate(json_activities):
        if val['id'] in registered_activities:
            to_remove.append(idx)

    new_activities = [val for idx, val in enumerate(json_activities) if idx not in to_remove]

    new_activities = list(map( lambda x: flattenjson( x, "__" ), new_activities ))

    conn = psycopg2.connect(f'dbname={DB["dbname"]} user=' + getpass.getuser())
    cur = conn.cursor()

    gear_df = get_data(DB, 'gear_types')

    for idx, activity in enumerate(new_activities):

        if type(activity['endTime']) == str and type(activity['endPosition__coordinates'][0]) == float:

            start_datetime = dt.strptime(activity['startTime'], '%Y-%m-%dT%H:%M:%S.%fZ')

            bottomdepthinmeters = get_bottom_depth(start_datetime,TOKTLOGGER)

            start_datetime_seconds_precision = activity['startTime'].split('.')[0]
            eventDate = activity['startTime'].split('T')[0]
            eventTime = activity['startTime'].split('T')[1].split('.')[0]
            # DON'T RUN IF NO END TIME
            endDate = activity['endTime'].split('T')[0]
            endTime = activity['endTime'].split('T')[1].split('.')[0]

            if activity['activityTypeName'] in gear_df['imr_name'].values:
                geartype = gear_df.loc[gear_df['imr_name'] == activity['activityTypeName'], 'geartype'].item()
            else:
                geartype = ''

            count = activity['activityNumber']
            readable_id = 'Activity_'+str(count)

            decimalLatitude = round_4dp(activity['startPosition__coordinates'][0])
            endDecimalLatitude = round_4dp(activity['endPosition__coordinates'][0])
            decimalLongitude = round_4dp(activity['startPosition__coordinates'][1])
            endDecimalLongitude = round_4dp(activity['endPosition__coordinates'][1])

            created = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            modified = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            history = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record created by pulling from Toktlogger")
            source = "Toktlogger"

            exe_str = f'''INSERT INTO metadata_catalogue_{CRUISE_NUMBER}
            (id,
            eventid,
            catalognumber,
            statid,
            eventdate,
            eventtime,
            enddate,
            endtime,
            decimallatitude,
            decimallongitude,
            enddecimallatitude,
            enddecimallongitude,
            bottomdepthinmeters,
            comments1,
            geartype,
            created,
            modified,
            history,
            source)
            VALUES
            ('{activity["id"]}',
            '{activity["id"]}',
            '{readable_id}',
            {activity["localstationNumber"]},
            '{eventDate}',
            '{eventTime}',
            '{endDate}',
            '{endTime}',
            {decimalLatitude},
            {decimalLongitude},
            {endDecimalLatitude},
            {endDecimalLongitude},
            {bottomdepthinmeters},
            '{activity["comment"]}',
            '{geartype}',
            '{created}',
            '{modified}',
            '{history}',
            '{source}');'''

            cur.execute(exe_str)

    conn.commit()

    activities_df = get_registered_activities(DB, CRUISE_NUMBER)

    cur.close()
    conn.close()

    return activities_df
