import psycopg2
import psycopg2.extras
import pandas as pd
from website.lib.get_data import df_from_database

def init_metadata_catalogue(DB, CRUISE_NUMBER, cur, metadata_columns_dict):
    '''
    Creating the metadata catalogue table within the database to be used for the cruise.

    A new table will be created for each cruise, but within the same database.

    DBNAME: string
        Name of the database within which the tables will be created
    CRUISE_NUMBER: string
        Cruise number
    cur: cursor object
        PSQL cursor object
    metadata_columns_dict: dict
        dict of fields to use as column headers in the metadata catalogue table and specifications
    '''

    cur.execute("CREATE EXTENSION IF NOT EXISTS hstore;")

    exe_str = f"CREATE TABLE IF NOT EXISTS metadata_catalogue_{CRUISE_NUMBER} (id uuid PRIMARY KEY, "

    for field, vals in metadata_columns_dict.items():
        if field != 'id':
            exe_str = exe_str + field + " " + vals['format'] + ", "

    exe_str = exe_str + "other hstore, metadata hstore)"

    cur.execute(exe_str)

def init_stations(DB, CRUISE_NUMBER, cur):
    cur.execute(f"CREATE TABLE IF NOT EXISTS stations_{CRUISE_NUMBER} (id uuid PRIMARY KEY, stationName text, decimalLatitude double precision, decimalLongitude double precision, comment text, created timestamp with time zone)")

    df = pd.read_csv('website/config/dropdown_initial_values/stationName.csv')
    for idx, row in df.iterrows():
        id = row['id']
        stationName = row['stationName']
        decimalLongitude = row['decimalLongitude']
        decimalLatitude = row['decimalLatitude']
        comment = row['comment']
        cur.execute(f"INSERT INTO stations_{CRUISE_NUMBER} (id, stationName, decimalLongitude, decimalLatitude, comment, created) SELECT '{id}', '{stationName}', {decimalLongitude}, {decimalLatitude}, '{comment}', CURRENT_TIMESTAMP WHERE NOT EXISTS (SELECT stationName FROM stations_{CRUISE_NUMBER} WHERE stationName = '{stationName}');")

def init_personnel(DB, CRUISE_NUMBER, cur):
    cur.execute(f"CREATE TABLE IF NOT EXISTS personnel_{CRUISE_NUMBER} (id uuid PRIMARY KEY, personnel text, first_name text, last_name text, institution text, email text, orcid text, comment text, created timestamp with time zone)")

    df = pd.read_csv('website/config/dropdown_initial_values/personnel.csv')

    for idx, row in df.iterrows():
        id = row['id']
        first_name = row['first_name']
        last_name = row['last_name']
        email = row['email']
        personnel = f"{first_name} {last_name} ({email})"
        institution = row['institution']
        orcid = row['orcid']
        comment = row['comment']
        cur.execute(f"INSERT INTO personnel_{CRUISE_NUMBER} (id, personnel, first_name, last_name, institution, email, orcid, comment, created) SELECT '{id}', '{personnel}', '{first_name}','{last_name}','{institution}','{email}','{orcid}','{comment}', CURRENT_TIMESTAMP WHERE NOT EXISTS (SELECT email FROM personnel_{CRUISE_NUMBER} WHERE email = '{email}');")

def init_user_field_setups(DB, CRUISE_NUMBER, cur):
    '''
    Creating a table to log different setups when users select fields to use for various sample types.
    '''
    cur.execute(f"CREATE TABLE IF NOT EXISTS user_field_setups_{CRUISE_NUMBER} (setupName text PRIMARY KEY, setup json, created timestamp with time zone)")

    setup = {
    'parentID': 'same',
    'sampleType': 'same',
    'pi_details': 'same',
    'recordedBy': 'same',
    'id': 'vary',
    'catalogNumber': 'vary',
    'samplingProtocolDoc': 'same',
    'samplingProtocolSection': 'same',
    'samplingProtocolVersion': 'same',
    'comments1': 'vary',
    }

    setup = str(setup).replace('\'','"')

    # ONLY IF DOESN'T EXIST ALREADY
    exe_str = f"INSERT INTO user_field_setups_{CRUISE_NUMBER} (setupName, setup, created) SELECT 'temporary', '{setup}', CURRENT_TIMESTAMP WHERE NOT EXISTS (SELECT setupName FROM user_field_setups_{CRUISE_NUMBER} WHERE setupName = 'temporary');"
    cur.execute(exe_str)

def check_if_cruise_exists(DB, CRUISE_NUMBER):
    query = f"SELECT cruise_number FROM cruises WHERE cruise_number = '{CRUISE_NUMBER}'"
    df = df_from_database(query, DB)
    if len(df) == 1:
        return True
    elif len(df) == 0:
        return False
    elif len(df) > 1:
        print('Multiple cruises logged with the same cruise number')
        return True

def run(DB, CRUISE_NUMBER, metadata_columns_dict):

    print('Initialising database tables for the cruise')
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    init_personnel(DB, CRUISE_NUMBER, cur)
    init_stations(DB, CRUISE_NUMBER, cur)
    init_user_field_setups(DB, CRUISE_NUMBER, cur)
    init_metadata_catalogue(DB, CRUISE_NUMBER, cur, metadata_columns_dict)
    conn.commit()
    cur.close()
    conn.close()
