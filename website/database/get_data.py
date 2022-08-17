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
    return df

def get_registered_activities(DBNAME, METADATA_CATALOGUE):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f'SELECT * FROM {METADATA_CATALOGUE} where parentid is NULL;', con=conn)
    return df

def get_personnel_list(DBNAME=False, table='personnel'):
    if DBNAME == False:
        df_personnel = pd.read_csv(f'website/database/{table}.csv')
    else:
        df_personnel = get_data(DBNAME, table)
    df_personnel.sort_values(by='last_name', inplace=True)
    df_personnel['personnel'] = df_personnel['first_name'] + ' ' + df_personnel['last_name'] + ' (' + df_personnel['email'] + ')'
    personnel = list(df_personnel['personnel'])
    return personnel
