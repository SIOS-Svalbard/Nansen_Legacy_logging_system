import psycopg2
import psycopg2.extras
import pandas as pd

def df_from_database(query, DB):
    conn = psycopg2.connect(**DB)
    cursor = conn.cursor()
    cursor.execute(query)
    # Fetch all the rows from the result set
    rows = cursor.fetchall()

    # Get the column names from the cursor description
    column_names = [desc[0] for desc in cursor.description]

    # Create a DataFrame from the fetched rows
    df = pd.DataFrame(rows, columns=column_names)
    # Close the cursor and the database connection
    cursor.close()
    conn.close()
    return df

def get_cruise(DB):
    query = f'SELECT * FROM cruises WHERE current = true'
    df = df_from_database(query, DB)

    if len(df) == 0:
        return None
    elif len(df) == 1:
        return df
    else:
        print('Multiple active cruises')
        print(df)
        return df

def get_cruises(DB):
    query = f'SELECT cruise_number FROM cruises'
    df = df_from_database(query, DB)
    return df['cruise_number'].astype(str).values

def get_data(DB, table):
    query = f'SELECT * FROM {table}'
    df = df_from_database(query, DB)
    if "comment" in list(df.columns):
        df.loc[df["comment"] == "nan", "comment"] = ""
    return df

def get_institutions_list(DB):
    query = f'SELECT full_name FROM institutions'
    df = df_from_database(query, DB)
    return df['full_name'].tolist()

def get_all_ids(DB, CRUISE_NUMBER):
    query = f'SELECT id FROM metadata_catalogue_{CRUISE_NUMBER};'
    df = df_from_database(query, DB)
    return df['id'].tolist()

def get_all_sources(DB, CRUISE_NUMBER):
    query = f'SELECT recordsource FROM metadata_catalogue_{CRUISE_NUMBER} GROUP BY recordsource;'
    df = df_from_database(query, DB)
    sources = df['recordsource'].tolist()
    files = [source.split('filename ')[1] for source in sources if 'filename' in source]
    return files

def get_registered_activities(DB, CRUISE_NUMBER):
    query = f"""
    SELECT
        *,
        (
            SELECT COUNT(*)
            FROM metadata_catalogue_{CRUISE_NUMBER} ch
            WHERE p.id=ch.parentid
        ) AS number_of_children
    FROM metadata_catalogue_{CRUISE_NUMBER} p
    WHERE parentid is NULL;
    """
    df = df_from_database(query, DB)
    return df

def get_registered_niskins(DB, CRUISE_NUMBER):
    query = f"""
    SELECT
        *,
        (
            SELECT COUNT(*)
            FROM metadata_catalogue_{CRUISE_NUMBER} ch
            WHERE p.id=ch.parentid
        ) AS number_of_children
    FROM metadata_catalogue_{CRUISE_NUMBER} p
    WHERE sampletype = 'Niskin';
    """
    df = df_from_database(query, DB)
    return df

def get_metadata_for_list_of_ids(DB, CRUISE_NUMBER, ids):
    if len(ids) > 1:
        query = f'SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where id in {tuple(ids)};'
    else:
        query = f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where id = '{ids[0]}';"
    df = df_from_database(query, DB)
    return df

def get_metadata_for_id(DB, CRUISE_NUMBER, ID):
    if ID in ['addNew', None]:
        ID = '6818a630-3e44-11ed-bc56-07202a870ce3'
    query = f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where id = '{ID}';"
    df = df_from_database(query, DB)
    return df

def get_sampleType(DB, CRUISE_NUMBER, ID):
    query = f"SELECT sampletype FROM metadata_catalogue_{CRUISE_NUMBER} where id = '{ID}';"
    df = df_from_database(query, DB)
    sampleType = df['sampletype'].item()
    return sampleType

def get_metadata_for_record_and_ancestors(db, cruise_number, id):
    df = get_metadata_for_id(db, cruise_number, id)
    parentid = df["parentid"].item()
    while parentid:
        parent_df = get_metadata_for_id(db, cruise_number, parentid)
        df = pd.concat([df, parent_df], ignore_index=True)
        parentid = parent_df["parentid"].item()
    return df

def get_children(DB, CRUISE_NUMBER, ids):
    if len(ids) == 1:
        id = ids[0]
        query = f'''
        SELECT
        *,
        (
            SELECT COUNT(*)
            FROM metadata_catalogue_{CRUISE_NUMBER} ch
            WHERE p.id=ch.parentid
        ) AS number_of_children
        FROM metadata_catalogue_{CRUISE_NUMBER} p
        where parentid = '{id}';'''
    else:
        query = f'''
        SELECT
        *,
        (
            SELECT COUNT(*)
            FROM metadata_catalogue_{CRUISE_NUMBER} ch
            WHERE p.id=ch.parentid
        ) AS number_of_children
        FROM metadata_catalogue_{CRUISE_NUMBER} p
        where parentid in {tuple(ids)};'''
    df = df_from_database(query, DB)
    return df

def get_personnel_df(DB, CRUISE_NUMBER, table='personnel'):
    df_personnel = get_data(DB, f'{table}_{CRUISE_NUMBER}')
    df_personnel.sort_values(by='last_name', inplace=True)
    df_personnel['personnel'] = df_personnel['first_name'] + ' ' + df_personnel['last_name'] + ' (' + df_personnel['email'] + ')'
    return df_personnel

def get_personnel_list(DB=None, CRUISE_NUMBER=None, table='personnel'):
    df_personnel = get_personnel_df(DB=DB, CRUISE_NUMBER=CRUISE_NUMBER, table='personnel')
    personnel = list(df_personnel['personnel'])
    return personnel

def get_stations_list(DB=None, CRUISE_NUMBER=None, table='stations'):
    df_stations = get_data(DB, f'{table}_{CRUISE_NUMBER}')
    df_stations.sort_values(by='stationname', inplace=True)
    stations = list(df_stations['stationname'])
    return stations

def get_gears_list(DB=None, table='geartype'):
    df_gears = get_data(DB, table)
    df_gears.sort_values(by='geartype', inplace=True)
    gears = list(df_gears['geartype'])
    return gears

def get_user_setup(DB, CRUISE_NUMBER, setupName):
    query = f"SELECT setup from user_field_setups_{CRUISE_NUMBER} where setupName = '{setupName}'"
    df = df_from_database(query, DB)
    return df['setup'][0]

def get_samples_for_pi(DB, CRUISE_NUMBER, pi_email):
    query = f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where position ('{pi_email}' IN pi_email) <> 0;"
    df = df_from_database(query, DB)
    return df

def get_samples_for_recordedby(DB, CRUISE_NUMBER, recordedby_email):
    query = f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where position ('{recordedby_email}' IN recordedby_email) <> 0;"
    df = df_from_database(query, DB)
    return df

def get_samples_for_personnel(DB, CRUISE_NUMBER, personnel_email):
    query = f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where position ('{personnel_email}' IN recordedby_email) <> 0 or position ('{personnel_email}' IN pi_email) <> 0;"
    df = df_from_database(query, DB)
    return df

def get_samples_for_sampletype(DB, CRUISE_NUMBER, sampletype):
    query = f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where sampletype = '{sampletype}'"
    df = df_from_database(query, DB)
    return df

def get_subconfig_for_sampletype(sampleType, DB):
    try:
        if type(sampleType) != str:
            return 'Activities'
        if sampleType in ['','NULL','nan']:
            return 'Activities'
        else:
            df = get_data(DB, 'sampletype')
            subconfig = df.loc[df['sampletype'] == sampleType, 'subconfig'].iloc[0]
            return subconfig
    except:
        return 'Other'
