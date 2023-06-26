import pandas as pd
import os
import re
import uuid
import math
from website.lib.get_data import get_registered_activities, get_all_ids
from website.lib.propegate_parents_to_children import propegate_parents_to_children
from datetime import datetime as dt
from website.lib.input_update_records import insert_into_metadata_catalogue
from website.lib.get_dict_for_list_of_fields import get_dict_for_list_of_fields
from website import FIELDS_FILEPATH, CONFIG
from website.lib.get_setup_for_configuration import get_setup_for_configuration
from website.lib.other_functions import format_form_value

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
    return df_tmp.loc[df_tmp['geartype'].isin(['CTD w/bottles','CTD']), 'id'].item()


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

    (
        output_config_dict,
        output_config_fields,
        extra_fields_dict,
        cf_standard_names,
        dwc_terms,
        dwc_terms_not_in_config,
        all_fields_dict,
        added_fields_dic,
        added_cf_names_dic,
        added_dwc_terms_dic,
        groups
    ) = get_setup_for_configuration(
        fields_filepath=FIELDS_FILEPATH,
        subconfig='Niskin bottles',
        CRUISE_NUMBER=CRUISE_NUMBER
    )

    columns = list(output_config_dict['Data']['Required'].keys()) + list(output_config_dict['Data']['Recommended'].keys())
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

        for col in ['recordedBy', 'pi_details']:
            df_cruise.drop(col, axis=1, inplace=True)

        df_to_submit = propegate_parents_to_children(df_cruise, DB, CRUISE_NUMBER)

        df_to_submit.columns = df_to_submit.columns.str.lower()

        fields_to_submit_dict = {} # dictionary to populate with with fields, values and formatting requirements to submit to metadata catalogue table in database
        fields_to_submit_dict['columns'] = {}
        fields_to_submit_dict['hstore'] = {}
        metadata_columns_list = CONFIG["metadata_catalogue"]["fields_to_use_as_columns"]

        inherited_columns = df_to_submit.columns

        for requirement in output_config_dict['Data'].keys():
            if requirement not in ['Required CSV', 'Source']:
                for field, vals in output_config_dict['Data'][requirement].items():
                    if field.lower() in df_to_submit.columns:
                        if field in metadata_columns_list:
                            fields_to_submit_dict['columns'][field] = output_config_dict['Data'][requirement][field]
                            #print(field,df_to_submit[field.lower()])
                            fields_to_submit_dict['columns'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                        else:
                            fields_to_submit_dict['hstore'][field] = output_config_dict['Data'][requirement][field]
                            fields_to_submit_dict['hstore'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                        inherited_columns = [col for col in inherited_columns if col != field.lower()]

        for field, vals in added_fields_dic['Data'].items():
            if field.lower() in df_to_submit.columns:
                if field in metadata_columns_list:
                    fields_to_submit_dict['columns'][field] = vals
                    fields_to_submit_dict['columns'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                else:
                    fields_to_submit_dict['hstore'][field] = vals
                    fields_to_submit_dict['hstore'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                inherited_columns = [col for col in inherited_columns if col != field.lower()]

        for field, vals in added_dwc_terms_dic['Data'].items():
            if field.lower() in df_to_submit.columns:
                if field in metadata_columns_list:
                    fields_to_submit_dict['columns'][field] = vals
                    fields_to_submit_dict['columns'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                else:
                    fields_to_submit_dict['hstore'][field] = vals
                    fields_to_submit_dict['hstore'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                inherited_columns = [col for col in inherited_columns if col != field.lower()]

        for field, vals in added_cf_names_dic['Data'].items():
            if field.lower() in df_to_submit.columns:
                if field in metadata_columns_list:
                    fields_to_submit_dict['columns'][field] = vals
                    fields_to_submit_dict['columns'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                else:
                    fields_to_submit_dict['hstore'][field] = vals
                    fields_to_submit_dict['hstore'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                inherited_columns = [col for col in inherited_columns if col != field.lower()]

        inheritable = CONFIG["metadata_catalogue"]["fields_to_inherit"]
        weak = CONFIG["metadata_catalogue"]["fields_to_inherit_if_not_logged_for_children"]
        inherited_columns = [field for field in inherited_columns if field not in ['pi_name', 'pi_institution', 'pi_orcid', 'pi_email', 'recordedby_name', 'recordedby_email', 'recordedby_orcid', 'recordedby_institution']]
        inherited_columns = [field for field in inheritable+weak if field.lower() in inherited_columns]

        inherited_fields_dict = get_dict_for_list_of_fields(inherited_columns, FIELDS_FILEPATH)

        for field, vals in inherited_fields_dict.items():
            if field.lower() in df_to_submit.columns:
                if field in metadata_columns_list:
                    fields_to_submit_dict['columns'][field] = vals
                    fields_to_submit_dict['columns'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                else:
                    fields_to_submit_dict['hstore'][field] = vals
                    fields_to_submit_dict['hstore'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]

        record_details = get_dict_for_list_of_fields(['created','modified','history','recordSource'],FIELDS_FILEPATH)
        fields_to_submit_dict['columns']['created'] = record_details['created']
        fields_to_submit_dict['columns']['modified'] = record_details['modified']
        fields_to_submit_dict['columns']['history'] = record_details['history']
        fields_to_submit_dict['columns']['recordSource'] = record_details['recordSource']

        num_samples = len(df_to_submit)

        fields_to_submit_dict['columns']['created']['value'] = [dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") for n in range(int(num_samples))]
        fields_to_submit_dict['columns']['modified']['value'] = [dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") for n in range(int(num_samples))]
        fields_to_submit_dict['columns']['history']['value'] = [dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Metadata for Niskin bottle harvested from .btl file and parent CTD") for n in range(int(num_samples))]
        fields_to_submit_dict['columns']['recordSource']['value'] = ["Metadata for Niskin bottle harvested from .btl file and parent CTD" for n in range(int(num_samples))]

        insert_into_metadata_catalogue(fields_to_submit_dict, int(num_samples), DB, CRUISE_NUMBER)
