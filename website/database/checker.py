#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
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
import website.database.fields as fields
from website.other_functions.other_functions import split_personnel_list
import uuid

def checker(input_metadata, df_metadata_catalogue, DBNAME, ID):
    '''
    Checks data before they can be imported into the metadata catalogue

    input_metadata: Dictionary of fields and values, for example from an html form.
    df_metadata_catalogue: pandas dataframe of metadata catalogue
    DBNAME: name of the PostgreSQL database
    ID: ID of the sample being registered. Listed as 'addNew' if not assigned yet, e.g. for a new activity where the user wants the system to create the ID.
    '''

    # Append error messages to list.
    # If the list contains at least one error message after the checker has run, the record should be rejected
    errors = []

    df_metadata_catalogue['timestamp'] = pd.to_datetime(df_metadata_catalogue['eventdate'].astype(str)+' '+df_metadata_catalogue['eventtime'].astype(str))
    registered_event_timestamps= list(df_metadata_catalogue['timestamp'])

    # key is the field name, val is the value provided by the user that needs checking
    for key, val in input_metadata.items():

        # IDs
        ids = df_metadata_catalogue['id'].values

        # If any of required fields are blank, error and state what is missing.
        if key in ['eventDate', 'eventTime', 'stationName', 'decimalLatitude', 'decimalLongitude', 'pis', 'recordedBys', 'gearType']:
            if val == '':
                errors.append(f'{key} is required. Please provide a value.')

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
        if key in ['minimumDepthInMeters', 'maximumDepthInMeters', 'minimumElevationInMeters', 'maximumElevationInMeters']:
            if val != '':
                val = float(val)
                if 0 <= val <= 30000:
                    pass
                elif 30000 < float(val):
                    errors.append(f'{key} must be less than or equal to 30000')
                else:
                    errors.append(f'{key} must be a number greater than 0')

                if key == 'minimumDepthInMeters':
                    maxdepth = input_metadata['maximumDepthInMeters']
                    # Maybe sometimes only one depth (min or max) is known?
                    # if maxdepth == '':
                    #     errors.append('You have entered a minimum depth. Please also enter a maximum depth. They can be the same if a single depth was sampled.')
                    if maxdepth != '':
                        if val > float(maxdepth):
                            errors.append('Maximum depth must be greater than or equal to minimum depth')

                if key == 'minimumElevationInMeters':
                    maxelevation = input_metadata['maximumElevationInMeters']
                    if maxelevation != '':
                        if val > float(maxelevation):
                            errors.append('Maximum elevation must be greater than minimum elevation')

        # Dates and times
        if key == 'eventDate':
            if val != '' and input_metadata['eventTime'] != '':
                timestamp = dt.strptime(val + input_metadata['eventTime'], "%Y-%m-%d%H:%M:%S")
                if dt.utcnow() < timestamp:
                    errors.append('Time and date must be before current UTC time')

                # Not performing this check on activities when the metadata is being edited because obviously it is already registered in the system.
                if 'parentID' in input_metadata.keys():
                    if input_metadata['parentID'] == '' and timestamp in registered_event_timestamps and ID == 'addNew':
                        errors.append('Another activity has already been registered at the same date and time.')
                else:
                    if timestamp in registered_event_timestamps and ID == 'addNew':
                        errors.append('Another activity has already been registered at the same date and time.')

        if key == 'middleDate': # What is they provide date and not time or vice versa?
            if val != '':
                timestamp_mid = dt.strptime(val + input_metadata['middleTime'], "%Y-%m-%d%H:%M:%S")
                if dt.utcnow() < timestamp_mid:
                    errors.append('Time and date must be before current UTC time')
                timestamp_start = dt.strptime(input_metadata['eventDate'] + input_metadata['eventTime'], "%Y-%m-%d%H:%M:%S")
                if timestamp_start > timestamp_mid:
                    errors.append('Mid time must be after the start time')


        if key == 'endDate': # What is they provide date and not time or vice versa?
            if val != '':
                timestamp_end = dt.strptime(val + input_metadata['endTime'], "%Y-%m-%d%H:%M:%S")
                if dt.utcnow() < timestamp_end:
                    errors.append('Time and date must be before current UTC time')
                timestamp_start = dt.strptime(input_metadata['eventDate'] + input_metadata['eventTime'], "%Y-%m-%d%H:%M:%S")
                if timestamp_start > timestamp_end:
                    errors.append('End time must be after the start time')
                try:
                    timestamp_mid = dt.strptime(input_metadata['middleDate'] + input_metadata['middleTime'], "%Y-%m-%d%H:%M:%S")
                    if timestamp_mid > timestamp_end:
                        errors.append('End time must be after the middle time')
                except:
                    pass

        # Personnel
        if key in ['pis', 'recordedBys']:

            df_personnel = get_data(DBNAME, 'personnel')
            df_personnel.sort_values(by='last_name', inplace=True)
            df_personnel['personnel'] = df_personnel['first_name'] + ' ' + df_personnel['last_name'] + ' (' + df_personnel['email'] + ')'
            personnel = list(df_personnel['personnel'])
            for person in val:
                if person not in personnel:
                    if person != '':
                        errors.append(f'{person} is not registered in the system. You may need to register a new person first.')

        # Values from lists
        if key == 'gearType':

            df_gears = get_data(DBNAME, 'gear_types')
            df_gears.sort_values(by='geartype', inplace=True)
            gearTypes = list(df_gears['geartype'])

            if val not in gearTypes:
                errors.append('Please select a gear type registered in the system. You may need to register a new gear type first.')

        if key == 'sampleType':

            if val != '':
                df_samples = get_data(DBNAME, 'sample_types')
                df_samples.sort_values(by='sampletype', inplace=True)
                sampleTypes = list(df_samples['sampletype'])

                if val not in sampleTypes:
                    errors.append('Please select a sample type registered in the system. You may need to register a new sample type first.')

        if key == 'intendedMethod':

            if val != '':
                df_intendmethods = get_data(DBNAME, 'intended_methods')
                df_intendmethods.sort_values(by='intendedmethod', inplace=True)
                intendedMethods = list(df_intendedmethods['intendedmethod'])

                if val not in intendedMethods:
                    errors.append('Please select an intended method registered in the system. You may need to register a new intended method first.')

        if key == 'stationName':

            df_stations = get_data(DBNAME, 'stations')
            df_stations.sort_values(by='stationname', inplace=True)
            stationNames = list(df_stations['stationname'])

            if val not in stationNames:
                errors.append('Please select a station name from the drop-down list. You may need to register a new station name first.')

    n = 0
    for key in ['minimumDepthInMeters', 'maximumDepthInMeters', 'minimumElevationInMeters', 'maximumElevationInMeters']:
        if input_metadata[key] == '':
            n = n + 1
    if n == 4:
        errors.append('Please include an elevation or depth (preferably both minimum and maximum, they can be the same)')

    elif input_metadata['minimumDepthInMeters'] != '' or input_metadata['maximumDepthInMeters'] != '':
        if input_metadata['minimumElevationInMeters'] != '' or input_metadata['maximumElevationInMeters'] != '':
            errors.append('It is not possible to enter an elevation and a depth.')

    return errors
