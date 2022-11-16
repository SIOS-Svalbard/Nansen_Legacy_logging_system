import psycopg2
import psycopg2.extras
import getpass
import pandas as pd

def get_cruise(DBNAME):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f'SELECT * FROM cruises WHERE current = true', con=conn)
    if len(df) == 0:
        return False
    elif len(df) == 1:
        return df
    else:
        print('Multiple active cruises')
        print(df)
        return df

def get_cruises(DBNAME):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f'SELECT cruise_number FROM cruises', con=conn)
    return df['cruise_number'].astype(str).values

def get_data(DBNAME, table):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f'SELECT * FROM {table}', con=conn)
    if "comment" in list(df.columns):
        df["comment"].loc[df["comment"] == "nan"] = ""
    return df

def get_all_ids(DBNAME, CRUISE_NUMBER):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f'SELECT id FROM metadata_catalogue_{CRUISE_NUMBER};', con=conn)
    return df['id'].tolist()

def get_registered_activities(DBNAME, CRUISE_NUMBER):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f'SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where parentid is NULL;', con=conn)
    return df

def get_metadata_for_list_of_ids(DBNAME, CRUISE_NUMBER, ids):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    if len(ids) > 1:
        df = pd.read_sql(f'SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where id in {tuple(ids)};', con=conn)
    else:
        df = pd.read_sql(f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where id = '{ids[0]}';", con=conn)
    return df

def get_metadata_for_id(DBNAME, CRUISE_NUMBER, ID):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    if ID == 'addNew':
        ID = '6818a630-3e44-11ed-bc56-07202a870ce3'
    df = pd.read_sql(f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where id = '{ID}';", con=conn)
    return df

def get_children(DBNAME, CRUISE_NUMBER, ids):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    if len(ids) == 1:
        id = ids[0]
        df = pd.read_sql(f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where parentid = '{id}';", con=conn)
    else:
        df = pd.read_sql(f'SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where parentid in {tuple(ids)};', con=conn)
    return df

def get_personnel_df(DBNAME=False, CRUISE_NUMBER=False, table='personnel'):
    if DBNAME == False:
        df_personnel = pd.read_csv(f'website/database/{table}.csv')
    else:
        df_personnel = get_data(DBNAME, table+'_'+CRUISE_NUMBER)
    df_personnel.sort_values(by='last_name', inplace=True)
    df_personnel['personnel'] = df_personnel['first_name'] + ' ' + df_personnel['last_name'] + ' (' + df_personnel['email'] + ')'
    return df_personnel

def get_personnel_list(DBNAME=False, CRUISE_NUMBER=False, table='personnel'):
    df_personnel = get_personnel_df(DBNAME=DBNAME, CRUISE_NUMBER=CRUISE_NUMBER, table='personnel')
    personnel = list(df_personnel['personnel'])
    return personnel

def get_user_setup(DBNAME, CRUISE_NUMBER, setupName):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f"SELECT setup from user_field_setups_{CRUISE_NUMBER} where setupName = '{setupName}'", con=conn)
    return df['setup'][0]

def get_samples_for_pi(DBNAME, CRUISE_NUMBER, pi_email):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where position ('{pi_email}' IN pi_email) <> 0;", con=conn)
    return df

def get_samples_for_recordedby(DBNAME, CRUISE_NUMBER, recordedby_email):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where position ('{recordedby_email}' IN recordedby_email) <> 0;", con=conn)
    return df

def get_samples_for_personnel(DBNAME, CRUISE_NUMBER, personnel_email):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where position ('{personnel_email}' IN recordedby_email) <> 0 or position ('{personnel_email}' IN pi_email) <> 0;", con=conn)
    return df

def get_samples_for_sampletype(DBNAME, CRUISE_NUMBER, sampletype):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f"SELECT * FROM metadata_catalogue_{CRUISE_NUMBER} where sampletype = '{sampletype}'", con=conn)
    return df
