import psycopg2
import psycopg2.extras
import pandas as pd

def get_cruise(DB):
    conn = psycopg2.connect(**DB)
    df = pd.read_sql(f'SELECT * FROM cruises WHERE current = true', con=conn)

    if len(df) == 0:
        return None
    elif len(df) == 1:
        return df
    else:
        print('Multiple active cruises')
        print(df)
        return df

def get_cruises(DB):
    conn = psycopg2.connect(**DB)
    df = pd.read_sql(f'SELECT cruise_number FROM cruises', con=conn)
    return df['cruise_number'].astype(str).values

def get_data(DB, table):
    conn = psycopg2.connect(**DB)
    df = pd.read_sql(f'SELECT * FROM {table}', con=conn)
    if "comment" in list(df.columns):
        df["comment"].loc[df["comment"] == "nan"] = ""
    return df

def get_all_ids(DB, CRUISE_NUMBER):
    conn = psycopg2.connect(**DB)
    df = pd.read_sql(f'SELECT id FROM metadata_catalogue_{CRUISE_NUMBER};', con=conn)
    return df['id'].tolist()

def get_registered_activities(DB, CRUISE_NUMBER):
    conn = psycopg2.connect(**DB)
    df = pd.read_sql(f'SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where parentid is NULL;', con=conn)
    return df

def get_metadata_for_list_of_ids(DB, CRUISE_NUMBER, ids):
    conn = psycopg2.connect(**DB)
    if len(ids) > 1:
        df = pd.read_sql(f'SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where id in {tuple(ids)};', con=conn)
    else:
        df = pd.read_sql(f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where id = '{ids[0]}';", con=conn)
    return df

def get_metadata_for_id(DB, CRUISE_NUMBER, ID):
    conn = psycopg2.connect(**DB)
    if ID in ['addNew', None]:
        ID = '6818a630-3e44-11ed-bc56-07202a870ce3'
    df = pd.read_sql(f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where id = '{ID}';", con=conn)
    return df

def get_metadata_for_record_and_ancestors(db, cruise_number, id):
    df = get_metadata_for_id(db, cruise_number, id)
    parentid = df["parentid"].item()
    while parentid:
        parent_df = get_metadata_for_id(db, cruise_number, parentid)
        df = pd.concat([df, parent_df], ignore_index=True)
        parentid = parent_df["parentid"].item()
    return df

def get_children(DB, CRUISE_NUMBER, ids):
    conn = psycopg2.connect(**DB)
    if len(ids) == 1:
        id = ids[0]
        df = pd.read_sql(f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where parentid = '{id}';", con=conn)
    else:
        df = pd.read_sql(f'SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where parentid in {tuple(ids)};', con=conn)
    return df

def get_personnel_df(DB=None, CRUISE_NUMBER=None, table='personnel'):
    if DB == None:
        df_personnel = pd.read_csv(f'website/templategenerator/website/config/{table}.csv')
    else:
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

def get_user_setup(DB, CRUISE_NUMBER, setupName):
    conn = psycopg2.connect(**DB)
    df = pd.read_sql(f"SELECT setup from user_field_setups_{CRUISE_NUMBER} where setupName = '{setupName}'", con=conn)
    return df['setup'][0]

def get_samples_for_pi(DB, CRUISE_NUMBER, pi_email):
    conn = psycopg2.connect(**DB)
    df = pd.read_sql(f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where position ('{pi_email}' IN pi_email) <> 0;", con=conn)
    return df

def get_samples_for_recordedby(DB, CRUISE_NUMBER, recordedby_email):
    conn = psycopg2.connect(**DB)
    df = pd.read_sql(f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where position ('{recordedby_email}' IN recordedby_email) <> 0;", con=conn)
    return df

def get_samples_for_personnel(DB, CRUISE_NUMBER, personnel_email):
    conn = psycopg2.connect(**DB)
    df = pd.read_sql(f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where position ('{personnel_email}' IN recordedby_email) <> 0 or position ('{personnel_email}' IN pi_email) <> 0;", con=conn)
    return df

def get_samples_for_sampletype(DB, CRUISE_NUMBER, sampletype):
    conn = psycopg2.connect(**DB)
    df = pd.read_sql(f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where sampletype = '{sampletype}'", con=conn)
    return df
