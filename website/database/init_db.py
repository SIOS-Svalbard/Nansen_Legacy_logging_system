#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 10 08:46:31 2022

@author: lukem

Precursors:
    Create PSQL database called 'lfnl_db'
    Assign users as well as default postgres will all privileges on the database:
        GRANT ALL PRIVILIGES ON DATABASE lfnl_db TO username;

"""

import psycopg2
import psycopg2.extras
import getpass
import website.database.fields as fields
import pandas as pd

def create_database(DBNAME):
    '''
    Initialising the database if it doesn't already exist.

    A single database will run on the vessel for all cruises, so that the tables within can be used for future cruises.
    This allows someone to log a station name on one cruise and use it again on the next cruise for example.

    DBNAME: string
            Name of the database to be created
    '''

    conn = psycopg2.connect(database='postgres', user=getpass.getuser())
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute('SELECT datname FROM pg_database;')
    list_databases = cur.fetchall()

    # Initialise database if doesn't exist
    if (DBNAME,) in list_databases:
        print(f'Database {DBNAME} already exists')
    else:
        print('Creating database...')
        cur.execute(f'CREATE database {DBNAME}')
        cur.close()
        conn.close() # CREATE DATABASE cannot be executed inside a transaction block, so disconnecting and reconnecting

        conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
        cur = conn.cursor()

        # Creating tables and adding some values
        init_institutions(DBNAME, cur)
        init_stations(DBNAME, cur)
        init_sample_types(DBNAME, cur)
        init_gear_types(DBNAME, cur)
        init_intended_methods(DBNAME, cur)
        init_projects(DBNAME, cur)
        init_personnel(DBNAME, cur)
        init_storage_temperatures(DBNAME, cur)
        init_filters(DBNAME, cur)
        init_sex(DBNAME, cur)
        init_kingdoms(DBNAME, cur)

        conn.commit()
        cur.close()
        conn.close()
        print(f'Database created with name {DBNAME}')

def init_institutions(DBNAME, cur):
    cur.execute("CREATE TABLE institutions (id uuid PRIMARY KEY, short_name text, full_name text, comment text, date_added timestamp with time zone)")
    df = pd.read_csv('website/database/institutions.csv')
    for idx, row in df.iterrows():
        id = row['id']
        short_name = row['short_name']
        full_name = row['full_name']
        comment = row['comment']
        cur.execute(f"INSERT INTO institutions (id, short_name, full_name, comment, date_added) VALUES ('{id}', '{short_name}', '{full_name}', '{comment}', CURRENT_TIMESTAMP);")

def init_stations(DBNAME, cur):
    cur.execute("CREATE TABLE stations (id uuid PRIMARY KEY, stationName text, decimalLatitude double precision, decimalLongitude double precision, comment text, date_added timestamp with time zone)")
    df = pd.read_csv('website/database/stations.csv')
    for idx, row in df.iterrows():
        id = row['id']
        stationName = row['stationName']
        decimalLongitude = row['decimalLongitude']
        decimalLatitude = row['decimalLatitude']
        comment = row['comment']
        cur.execute(f"INSERT INTO stations (id, stationName, decimalLongitude, decimalLatitude, comment, date_added) VALUES ('{id}', '{stationName}', {decimalLongitude}, {decimalLatitude}, '{comment}', CURRENT_TIMESTAMP);")

def init_sample_types(DBNAME, cur):
    cur.execute("CREATE TABLE sample_types (id uuid PRIMARY KEY, sampleType text, comment text, date_added timestamp with time zone)")
    df = pd.read_csv('website/database/sample_types.csv')
    for idx, row in df.iterrows():
        id = row['id']
        sampleType = row['sampleType']
        comment = row['comment']
        cur.execute(f"INSERT INTO sample_types (id, sampleType, comment, date_added) VALUES ('{id}','{sampleType}','{comment}', CURRENT_TIMESTAMP);")

def init_gear_types(DBNAME, cur):
    cur.execute("CREATE TABLE gear_types (id uuid PRIMARY KEY, gearType text, comment text, date_added timestamp with time zone)")
    df = pd.read_csv('website/database/gear_types.csv')
    for idx, row in df.iterrows():
        id = row['id']
        gearType = row['gearType']
        comment = row['comment']
        cur.execute(f"INSERT INTO gear_types (id, gearType, comment, date_added) VALUES ('{id}','{gearType}','{comment}', CURRENT_TIMESTAMP);")

def init_intended_methods(DBNAME, cur):
    cur.execute("CREATE TABLE intended_methods (id uuid PRIMARY KEY, intendedMethod text, comment text, date_added timestamp with time zone)")
    df = pd.read_csv('website/database/intended_methods.csv')
    for idx, row in df.iterrows():
        id = row['id']
        intendedMethod = row['intendedMethod']
        comment = row['comment']
        cur.execute(f"INSERT INTO intended_methods (id, intendedMethod, comment, date_added) VALUES ('{id}', '{intendedMethod}', '{comment}', CURRENT_TIMESTAMP);")

def init_projects(DBNAME, cur):
    cur.execute("CREATE TABLE projects (id uuid PRIMARY KEY, project text, comment text, date_added timestamp with time zone)")
    df = pd.read_csv('website/database/projects.csv')
    for idx, row in df.iterrows():
        id = row['id']
        project = row['project']
        comment = row['comment']
        cur.execute(f"INSERT INTO projects (id, project, comment, date_added) VALUES ('{id}', '{project}', '{comment}', CURRENT_TIMESTAMP);")

def init_personnel(DBNAME, cur):
    cur.execute("CREATE TABLE personnel (id uuid PRIMARY KEY, first_name text, last_name text, institution text, email text, comment text, date_added timestamp with time zone)")
    df = pd.read_csv('website/database/personnel.csv')
    for idx, row in df.iterrows():
        id = row['id']
        first_name = row['first_name']
        last_name = row['last_name']
        institution = row['institution']
        email = row['email']
        comment = row['comment']
        cur.execute(f"INSERT INTO personnel (id, first_name, last_name, institution, email, comment, date_added) VALUES ('{id}', '{first_name}','{last_name}','{institution}','{email}','{comment}', CURRENT_TIMESTAMP);")

def init_storage_temperatures(DBNAME, cur):
    cur.execute("CREATE TABLE storage_temperatures (id uuid PRIMARY KEY, storageTemp text, comment text, date_added timestamp with time zone)")
    df = pd.read_csv('website/database/storage_temperatures.csv')
    for idx, row in df.iterrows():
        id = row['id']
        storageTemp = row['storageTemp']
        comment = row['comment']
        cur.execute(f"INSERT INTO storage_temperatures (id, storageTemp, comment, date_added) VALUES ('{id}', '{storageTemp}','{comment}', CURRENT_TIMESTAMP);")

def init_filters(DBNAME, cur):
    cur.execute("CREATE TABLE filters (id uuid PRIMARY KEY, filter text, comment text, date_added timestamp with time zone)")
    df = pd.read_csv('website/database/filters.csv')
    for idx, row in df.iterrows():
        id = row['id']
        filter = row['filter']
        comment = row['comment']
        cur.execute(f"INSERT INTO filters (id, filter, comment, date_added) VALUES ('{id}','{filter}','{comment}', CURRENT_TIMESTAMP);")

def init_sex(DBNAME, cur):
    cur.execute("CREATE TABLE sex (id uuid PRIMARY KEY, sex text, comment text, date_added timestamp with time zone)")
    df = pd.read_csv('website/database/sex.csv')
    for idx, row in df.iterrows():
        id = row['id']
        sex = row['sex']
        comment = row['comment']
        cur.execute(f"INSERT INTO sex (id, sex, comment, date_added) VALUES ('{id}', '{sex}' ,'{comment}', CURRENT_TIMESTAMP);")

def init_kingdoms(DBNAME, cur):
    cur.execute("CREATE TABLE kingdoms (id uuid PRIMARY KEY, kingdom text, comment text, date_added timestamp with time zone)") # WHAT ABOUT OTHER CLASSIFICATIONS IN SPECIES?
    df = pd.read_csv('website/database/kingdoms.csv')
    for idx, row in df.iterrows():
        id = row['id']
        kingdom = row['kingdom']
        comment = row['comment']
        cur.execute(f"INSERT INTO kingdoms (id, kingdom, comment, date_added) VALUES ('{id}', '{kingdom}', '{comment}', CURRENT_TIMESTAMP);")

def create_metadata_catalogue(DBNAME, METADATA_CATALOGUE):
    '''
    Creating the metadata catalogue table within the database to be used for the cruise.

    A new table/metadata catalogue will be created for each cruise, but within the same database.

    DBNAME: string
        Name of the database within which the table will be created
    METADATA_CATALOGUE: string
        Name of the table to be created
    '''

    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS hstore;")

    exe_str = f"CREATE TABLE IF NOT EXISTS {METADATA_CATALOGUE} (id uuid PRIMARY KEY, "

    for field in fields.fields:
        if field['hstore'] == False and field['name'] != 'id':
            exe_str = exe_str + field['name'] + " " + field['format'] + ", "

    exe_str = exe_str + "other hstore, metadata hstore, created timestamp with time zone, modified timestamp with time zone, history text, source text)"

    cur.execute(exe_str)
    conn.commit()
    cur.close()
    conn.close()

def run(DBNAME, METADATA_CATALOGUE):
    create_database(DBNAME)
    create_metadata_catalogue(DBNAME, METADATA_CATALOGUE)
