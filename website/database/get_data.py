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

def get_registered_activities(DBNAME, METADATA_CATALOGUE):
    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    df = pd.read_sql(f'SELECT * FROM {METADATA_CATALOGUE} where parentid is NULL;', con=conn)
    return df
    