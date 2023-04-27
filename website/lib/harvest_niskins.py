import pandas as pd
import os
import re
import uuid
import math
from website.templategenerator.website.lib.get_configurations import get_config_fields
from website.database.get_data import get_registered_activities, get_all_ids
from website.database.propegate_parents_to_children import propegate_parents_to_children
import website.templategenerator.website.config.fields as fields
from datetime import datetime as dt
from website.database.input_update_records import insert_into_metadata_catalogue_df

# from website.database.checker import run as checker
# from flask import flash

def get_fields_lists(DB, CRUISE_NUMBER):
    '''
    Returns the fields required
    Parameters
    ----------
    DB: dict
        PSQL database details
    CRUISE_NUMBER: string
        Cruise number
    Returns
    ----------
    columns: list
        List of fields to be column headers
    required: list
        List of fields that are required to be logged. A subset of columns

    '''
    required_fields_dic, recommended_fields_dic, extra_fields_dic, groups = get_fields(configuration='activity', DB=DB, CRUISE_NUMBER=CRUISE_NUMBER)
    niskin_fields = {**required_fields_dic, **recommended_fields_dic} # Merging dictionarys
    columns = list(niskin_fields.keys())
    required = list(required_fields_dic.keys())

    if 'pi_details' in required:
        required.remove('pi_details')
    if 'recordedBy_details' in required:
        required.remove('recordedBy_details')

    return columns, required

def generate_UUID(id_url):
    '''
    Generates a v5 UUID. This can be repeatedly generated from the same string.
    Parameters
    ----------
    id_url : string, text to be used to generate UUID
    Returns
    -------
    Version 5 UUID, string
    '''
    return str(uuid.uuid5(uuid.NAMESPACE_URL,id_url))

def pull_columns(df_ctd,ctd_file, METADATA_CATALOGUE, BTL_FILES_FOLDER, registered_ids):
    '''
    Pull columns from .btl file to a pandas dataframe
    '''
    # Creating a new temporary file to read from as .btl file needs cleaning to be understood by Pandas.
    # Note that some columns that I am not interested in are still merged together.
    with open(BTL_FILES_FOLDER + ctd_file, 'r') as f:
        n = 0 # counter of lines in new temporary file
        try:
            os.remove('/tmp/'+ctd_file)
        except OSError:
            pass
        with open('/tmp/'+ctd_file, 'a') as tmpfile:
            for line in f: # Iterate over lines
                if not line.startswith('*') and not line.startswith('#'): # Ignore header rows
                    if 'sdev' not in line and 'Position' not in line:
                        line = line.replace('(avg)','') # Removing (avg) from end of line - not a column value
                        line = re.sub(r"^\s+", "", line) # Removing whitespace at beginning of line
                        if n == 0: # For header line only
                            line = re.sub("\s+", ",", line)
                        line = re.sub("\s\s+" , ",", line)
                        tmpfile.write(line+'\n')
                    n += 1

    data = pd.read_csv('/tmp/'+ctd_file, delimiter=',', usecols=['Bottle', 'PrDM'])

    df_ctd['bottleNumber'] = data['Bottle']
    df_ctd['minimumDepthInMeters'] = df_ctd['maximumDepthInMeters'] = data['PrDM']

    data['id'] = ''
    for index, row in data.iterrows():
        id_url = f'File {ctd_file} niskin bottle {row["Bottle"]} metadata catalogue {METADATA_CATALOGUE}'
        ID = generate_UUID(id_url)
        df_ctd['id'].iloc[index] = ID

    registered_niskins = df_ctd[df_ctd['id'].isin(registered_ids)].index

    df_ctd.drop(registered_niskins,inplace=True)

    return df_ctd

def find_parentID(statID, df_activities):
    '''
    Find parentID of the niskin bottle (the CTD)
    Every activity in the toktlogger is logged with a statID.
    The statID is in the filename of each btl file, so can use this to match the btl file to the activity
    Parameters
    ----------
    statID : string
        Local station number. Included in btl file name and also logged in toktlogger for each activity.
    df_activities : pandas dataframe
        Registered activities from metadata catalogue
    Returns
    -------
    Pandas dataframe column for parentID
    '''

    df_tmp = df_activities.loc[df_activities['statid'] == int(statID)]
    return df_tmp.loc[df_tmp['geartype'] == 'CTD w/bottles', 'id'].item()


def harvest_niskins(DB, CRUISE_NUMBER, BTL_FILES_FOLDER):
    '''
    Read data from Niskin files into a single pandas dataframe
    This dataframe can be used to create a sample log.
    Parameters
    -------
    DB: string
        Name of the PSQL database that includes the metadata catalogue
    CRUISE_NUMBER: string
        Cruise number
    BTL_FILES_FOLDER: string
        Filepath to where the .btl files (for Niskin bottles) are stored
    '''

    METADATA_CATALOGUE = 'metadata_catalogue_'+CRUISE_NUMBER

    columns, required = get_fields_lists(DB, CRUISE_NUMBER)
    df_cruise = pd.DataFrame(columns=columns)
    df_activities = get_registered_activities(DB, CRUISE_NUMBER)
    registered_statids = list(set(df_activities['statid']))
    registered_statids = [int(statid) for statid in registered_statids if math.isnan(statid) == False ]
    registered_statids = [str(r).zfill(4) for r in registered_statids]
    registered_ids = get_all_ids(DB, CRUISE_NUMBER)

    for ctd_file in sorted(os.listdir(BTL_FILES_FOLDER)):
        if ctd_file.endswith('.btl'):
            statID = ctd_file.split('.')[0].split('sta')[1]
            if statID in registered_statids:
                df_ctd = pd.DataFrame(columns=columns)
                df_ctd = pull_columns(df_ctd, ctd_file, METADATA_CATALOGUE, BTL_FILES_FOLDER, registered_ids)
                df_ctd['dataFilename'] = ctd_file
                df_ctd['parentID'] = find_parentID(statID, df_activities)
                df_cruise = df_cruise.append(df_ctd, ignore_index=True)

    # Only proceed if unregistered Niskin bottles. Registered bottles removed in pull_columns
    if len(df_cruise) > 0:

        df_cruise['gearType'] = 'Niskin'
        df_cruise['sampleType'] = 'Niskin'
        df_cruise['eventID'] = df_cruise['id']

        for col in ['recordedBy_details', 'pi_details']:
            df_cruise.drop(col, axis=1, inplace=True)

        df_cruise = propegate_parents_to_children(df_cruise, DB, METADATA_CATALOGUE)

        for field in fields.fields:
            if field['name'] in df_cruise.columns:
                if field['format'] in ['int', 'double precision', 'time', 'date']:
                    df_cruise[field['name']] = df_cruise[field['name']].replace([None, 'NULL'])
                    df_cruise[field['name']].fillna('NULL', inplace=True)
                if field['format'] == 'time':
                    df_cruise[field['name']] = df_cruise[field['name']].astype('object')
                    df_cruise[field['name']].fillna('NULL', inplace=True)
                elif field['format'] == 'int':
                    df_cruise[field['name']] = df_cruise[field['name']].astype(int)

        # good, errors = checker(
        #     data=df_cruise,
        #     metadata=False,
        #     required=required,
        #     DB=DB,
        #     METADATA_CATALOGUE=METADATA_CATALOGUE,
        #     new=True
        #     )
        #
        # if good == False:
        #     for error in errors:
        #         flash(error, category='error')
        # else:


        df_cruise['created'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        df_cruise['modified'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        df_cruise['history'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record created from metadata in btl files")
        df_cruise['source'] = "Record created from metadata in btl files"

        insert_into_metadata_catalogue_df(df_cruise, metadata_df=False, DB=DB, METADATA_CATALOGUE=METADATA_CATALOGUE)

        # flash('Niskin bottle metadata harvested', category='success')
