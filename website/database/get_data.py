import psycopg2
import psycopg2.extras
import getpass
import pandas as pd

def get_data(DBNAME, table):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f'SELECT * FROM {table}', con=conn)
    if "comment" in list(df.columns):
        df["comment"].loc[df["comment"] == "nan"] = ""
    return df

def get_all_ids(DBNAME, METADATA_CATALOGUE):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f'SELECT id FROM {METADATA_CATALOGUE};', con=conn)
    return df['id'].tolist()

def get_registered_activities(DBNAME, METADATA_CATALOGUE):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f'SELECT * FROM {METADATA_CATALOGUE} where parentid is NULL;', con=conn)
    return df

def get_metadata_for_list_of_ids(DBNAME, METADATA_CATALOGUE, ids):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    if len(ids) > 1:
        df = pd.read_sql(f'SELECT * FROM {METADATA_CATALOGUE} where id in {tuple(ids)};', con=conn)
    else:
        df = pd.read_sql(f"SELECT * FROM {METADATA_CATALOGUE} where id = '{ids[0]}';", con=conn)
    return df

def get_metadata_for_id(DBNAME, METADATA_CATALOGUE, ID):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    if ID == 'addNew':
        ID = '6818a630-3e44-11ed-bc56-07202a870ce3'
    df = pd.read_sql(f"SELECT * FROM {METADATA_CATALOGUE} where id = '{ID}';", con=conn)
    return df

def get_children(DBNAME, METADATA_CATALOGUE, ids):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    if len(ids) == 1:
        id = ids[0]
        df = pd.read_sql(f"SELECT * FROM {METADATA_CATALOGUE} where parentid = '{id}';", con=conn)
    else:
        df = pd.read_sql(f'SELECT * FROM {METADATA_CATALOGUE} where parentid in {tuple(ids)};', con=conn)
    return df

def get_personnel_df(DBNAME=False, table='personnel'):
    if DBNAME == False:
        df_personnel = pd.read_csv(f'website/database/{table}.csv')
    else:
        df_personnel = get_data(DBNAME, table)
    df_personnel.sort_values(by='last_name', inplace=True)
    df_personnel['personnel'] = df_personnel['first_name'] + ' ' + df_personnel['last_name'] + ' (' + df_personnel['email'] + ')'
    return df_personnel

def get_personnel_list(DBNAME=False, table='personnel'):
    df_personnel = get_personnel_df(DBNAME=DBNAME, table='personnel')
    personnel = list(df_personnel['personnel'])
    return personnel

def get_user_setup(DBNAME, setupName):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f"SELECT setup from user_field_setups where setupName = '{setupName}'", con=conn)
    return df['setup'][0]

def get_samples_for_pi(DBNAME, METADATA_CATALOGUE, pi_email):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f"SELECT * FROM {METADATA_CATALOGUE} where position ('{pi_email}' IN pi_email) <> 0;", con=conn)
    return df

def get_samples_for_recordedby(DBNAME, METADATA_CATALOGUE, recordedby_email):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f"SELECT * FROM {METADATA_CATALOGUE} where position ('{recordedby_email}' IN recordedby_email) <> 0;", con=conn)
    return df

def get_samples_for_personnel(DBNAME, METADATA_CATALOGUE, personnel_email):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f"SELECT * FROM {METADATA_CATALOGUE} where position ('{personnel_email}' IN recordedby_email) <> 0 or position ('{personnel_email}' IN pi_email) <> 0;", con=conn)
    return df

def get_samples_for_sampletype(DBNAME, METADATA_CATALOGUE, sampletype):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f"SELECT * FROM {METADATA_CATALOGUE} where sampletype = '{sampletype}'", con=conn)
    return df
