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
from website.database.get_data import get_data, get_registered_activities, get_all_ids
import website.database.fields as fields
import uuid

def checker(input_metadata, DBNAME, METADATA_CATALOGUE):
    '''
    Checks data before they can be imported into the metadata catalogue

    input_metadata: Dictionary of fields and values, for example from an html form.
    DBNAME: name of the database where the metadata catalogue is hosted
    METADATA_CATALOGUE: name of the table of the metadata catalogue in the database
    '''

    # Append error messages to list.
    # If the list contains at least one error message after the checker has run, the record should be rejected
    errors = []

    # key is the field name, val is the value provided by the user that needs checking
    for key, val in input_metadata.items():

        # IDs
        ids = get_all_ids(DBNAME, METADATA_CATALOGUE)['id'].values

        if key == 'id':
            if val != '':
                val = val.replace('+','-').replace('/','-')
                try:
                    uuid.UUID(val)
                except:
                    errors.append('Not a valid ID. Please use a UUID, e.g. 10621b76-94c0-4cf5-8aa9-64697205da7d')
            elif val in ids:
                errors.append('ID already registered')

        if key == 'parentID':
            if val != '':
                val = val.replace('+','-').replace('/','-')
                try:
                    uuid.UUID(val)
                except:
                    errors.append('Not a valid parent ID. Please use a UUID, e.g. 10621b76-94c0-4cf5-8aa9-64697205da7d')
            elif val not in ids:
                errors.append(f'Parent with the ID {val} has not been registered')

        # Coordinates
        if key in ['decimalLatitude', 'middleDecimalLatitude', 'endDecimalLongitude']:
            if val != '':
                if -90 <= float(val) <= 90:
                    continue
                else:
                    errors.append('Latitude must be between -90 and 90 degrees')

        if key in ['decimalLongitude', 'middleDecimalLongitude', 'endDecimalLongitude']:
            if val != '':
                if -180 <= float(val) <= 180:
                    continue
                else:
                    errors.append('Latitude must be between -180 and 180 degrees')

        # Depths and elevations

        # Dates and times

        # Personnel

        # Values from lists

#     if new_uuid == False:
#         flash('Invalid UUID. Enter a valid UUID or remove and one will be assigned automatically', category='error')
#     elif new_uuid in df_metadata_catalogue['id'].astype(str).values and new_uuid != eventID:
#         flash('Univerisally unique ID already registered. Please use a different one.', category='error')
#     elif stationName == '':
#         flash('Please select a station name from the drop-down list', category='error')
#     elif gearType == '':
#         flash('Please select a gear type from the drop-down list', category='error')
#     elif 'Choose...' in pis and len(pis) == 1:
#         flash('Please select at least one person as PI from the drop-down list', category='error')
#     elif 'Choose...' in recordedBys and len(recordedBys) == 1:
#         flash('Please select at least one person who was involved in recording this activity from the drop-down list', category='error')
#     elif endDate == '' and endTime != '':
#         flash('Please select an end time or remove the end date. Both or none are required.', category='error')
#     elif endDate != '' and endTime == '':
#         flash('Please select an end date or remove the end time. Both or none are required.', category='error')
#     elif endDateTime <= startDateTime:
#         flash('End date and time must be after the start date and time', category='error')
#     elif startDateTime >= dt.utcnow():
#         flash('Start date and time must be in the past', category='error')
#     elif endDateTime >= dt.utcnow() and endDateTime != dt(3000,1,1):
#         flash('End date and time must be in the past', category='error')
#     elif minDepthInMeters > maxDepthInMeters:
#         flash('Maximum depth must be greater than minimum depth', category='error')
#     elif minElevationInMeters > maxElevationInMeters:
#         flash('Maximum elevation must be greater than minimum elevation', category='error')
#     elif 'Choose...' in pis and len(pis) == 1:
#         flash('Please select at least one person as PI from the drop-down list', category='error')
#     elif 'Choose...' in recordedBys and len(recordedBys) == 1:
#         flash('Please select at least one person who was involved in recording this activity from the drop-down list', category='error')

    return errors
