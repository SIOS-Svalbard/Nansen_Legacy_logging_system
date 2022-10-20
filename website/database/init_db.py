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
import json

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
        init_user_field_setups(DBNAME, cur)

        conn.commit()
        cur.close()
        conn.close()
        print(f'Database created with name {DBNAME}')

def init_institutions(DBNAME, cur):
    cur.execute("CREATE TABLE institutions (id uuid PRIMARY KEY, short_name text, full_name text, comment text, created timestamp with time zone)")
    df = pd.read_csv('website/database/dropdown_initial_values/institutions.csv')
    for idx, row in df.iterrows():
        id = row['id']
        short_name = row['short_name']
        full_name = row['full_name']
        comment = row['comment']
        cur.execute(f"INSERT INTO institutions (id, short_name, full_name, comment, created) VALUES ('{id}', '{short_name}', '{full_name}', '{comment}', CURRENT_TIMESTAMP);")

def init_stations(DBNAME, cur):
    cur.execute("CREATE TABLE stations (id uuid PRIMARY KEY, stationName text, decimalLatitude double precision, decimalLongitude double precision, comment text, created timestamp with time zone)")
    df = pd.read_csv('website/database/dropdown_initial_values/stations.csv')
    for idx, row in df.iterrows():
        id = row['id']
        stationName = row['stationName']
        decimalLongitude = row['decimalLongitude']
        decimalLatitude = row['decimalLatitude']
        comment = row['comment']
        cur.execute(f"INSERT INTO stations (id, stationName, decimalLongitude, decimalLatitude, comment, created) VALUES ('{id}', '{stationName}', {decimalLongitude}, {decimalLatitude}, '{comment}', CURRENT_TIMESTAMP);")

def init_sample_types(DBNAME, cur):
    cur.execute("CREATE TABLE sample_types (id uuid PRIMARY KEY, sampleType text, comment text, grouping text, vocabLabel text, vocabURI text, created timestamp with time zone)")

    with open('website/database/dropdown_initial_values/sampleTypes.json', 'r') as f:
        data = json.load(f)

    for item in data:
        ID = item['id']
        sampleType = item['sampleType']
        comment = item['comment']
        group = item['group']
        vocabLabel = item['vocabLabel']
        vocabURI = item['vocabURI']
        cur.execute(f"INSERT INTO sample_types (id, sampleType, comment, grouping, vocabLabel, vocabURI, created) VALUES ('{ID}','{sampleType}','{comment}','{group}','{vocabLabel}','{vocabURI}', CURRENT_TIMESTAMP);")

def init_gear_types(DBNAME, cur):
    cur.execute("CREATE TABLE gear_types (id uuid PRIMARY KEY, gearType text, IMR_name text, comment text, grouping text, vocabLabel text, vocabURI text, recommendedSampleTypes text, recommendedChildSamples text, created timestamp with time zone)")

    with open('website/database/dropdown_initial_values/gearTypes.json', 'r') as f:
        data = json.load(f)

    for item in data:
        ID = item['id']
        gearType = item['gearType']
        IMR_name = item['IMR_name']
        comment = item['comment']
        group = item['group']
        vocabLabel = item['vocabLabel']
        vocabURI = item['vocabURI']
        recommendedSampleTypes = item['recommendedSampleTypes']
        recommendedChildSamples = item['recommendedChildren']['sampleTypes']

        cur.execute(f"INSERT INTO gear_types (id, gearType, IMR_name, comment, grouping, vocabLabel, vocabURI, recommendedSampleTypes, recommendedChildSamples, created) VALUES ('{ID}','{gearType}','{IMR_name}','{comment}','{group}','{vocabLabel}','{vocabURI}','{recommendedSampleTypes}','{recommendedChildSamples}', CURRENT_TIMESTAMP);")

def init_intended_methods(DBNAME, cur):
    cur.execute("CREATE TABLE intended_methods (id uuid PRIMARY KEY, intendedMethod text, comment text, created timestamp with time zone)")
    df = pd.read_csv('website/database/dropdown_initial_values/intended_methods.csv')
    for idx, row in df.iterrows():
        id = row['id']
        intendedMethod = row['intendedMethod']
        comment = row['comment']
        cur.execute(f"INSERT INTO intended_methods (id, intendedMethod, comment, created) VALUES ('{id}', '{intendedMethod}', '{comment}', CURRENT_TIMESTAMP);")

def init_projects(DBNAME, cur):
    cur.execute("CREATE TABLE projects (id uuid PRIMARY KEY, project text, comment text, created timestamp with time zone)")
    df = pd.read_csv('website/database/dropdown_initial_values/projects.csv')
    for idx, row in df.iterrows():
        id = row['id']
        project = row['project']
        comment = row['comment']
        cur.execute(f"INSERT INTO projects (id, project, comment, created) VALUES ('{id}', '{project}', '{comment}', CURRENT_TIMESTAMP);")

def init_personnel(DBNAME, cur):
    cur.execute("CREATE TABLE personnel (id uuid PRIMARY KEY, first_name text, last_name text, institution text, email text, orcid text, comment text, created timestamp with time zone)")
    df = pd.read_csv('website/database/dropdown_initial_values/personnel.csv')

    for idx, row in df.iterrows():
        id = row['id']
        first_name = row['first_name']
        last_name = row['last_name']
        institution = row['institution']
        email = row['email']
        orcid = row['orcid']
        comment = row['comment']
        cur.execute(f"INSERT INTO personnel (id, first_name, last_name, institution, email, orcid, comment, created) VALUES ('{id}', '{first_name}','{last_name}','{institution}','{email}','{orcid}','{comment}', CURRENT_TIMESTAMP);")

def init_storage_temperatures(DBNAME, cur):
    cur.execute("CREATE TABLE storage_temperatures (id uuid PRIMARY KEY, storageTemp text, comment text, created timestamp with time zone)")
    df = pd.read_csv('website/database/dropdown_initial_values/storage_temperatures.csv')
    for idx, row in df.iterrows():
        id = row['id']
        storageTemp = row['storageTemp']
        comment = row['comment']
        cur.execute(f"INSERT INTO storage_temperatures (id, storageTemp, comment, created) VALUES ('{id}', '{storageTemp}','{comment}', CURRENT_TIMESTAMP);")

def init_filters(DBNAME, cur):
    cur.execute("CREATE TABLE filters (id uuid PRIMARY KEY, filter text, comment text, created timestamp with time zone)")
    df = pd.read_csv('website/database/dropdown_initial_values/filters.csv')
    for idx, row in df.iterrows():
        id = row['id']
        filter = row['filter']
        comment = row['comment']
        cur.execute(f"INSERT INTO filters (id, filter, comment, created) VALUES ('{id}','{filter}','{comment}', CURRENT_TIMESTAMP);")

def init_sex(DBNAME, cur):
    cur.execute("CREATE TABLE sex (id uuid PRIMARY KEY, sex text, comment text, created timestamp with time zone)")
    df = pd.read_csv('website/database/dropdown_initial_values/sex.csv')
    for idx, row in df.iterrows():
        id = row['id']
        sex = row['sex']
        comment = row['comment']
        cur.execute(f"INSERT INTO sex (id, sex, comment, created) VALUES ('{id}', '{sex}' ,'{comment}', CURRENT_TIMESTAMP);")

def init_kingdoms(DBNAME, cur):
    cur.execute("CREATE TABLE kingdoms (id uuid PRIMARY KEY, kingdom text, comment text, created timestamp with time zone)") # WHAT ABOUT OTHER CLASSIFICATIONS IN SPECIES?
    df = pd.read_csv('website/database/dropdown_initial_values/kingdoms.csv')
    for idx, row in df.iterrows():
        id = row['id']
        kingdom = row['kingdom']
        comment = row['comment']
        cur.execute(f"INSERT INTO kingdoms (id, kingdom, comment, created) VALUES ('{id}', '{kingdom}', '{comment}', CURRENT_TIMESTAMP);")

def init_user_field_setups(DBNAME, cur):
    cur.execute("CREATE TABLE user_field_setups (setupName text PRIMARY KEY, setup json, created timestamp with time zone)")

    setup = {
    'parentID': 'same',
    'sampleType': 'same',
    'pi_details': 'same',
    'recordedBy_details': 'same',
    'id': 'vary',
    'catalogNumber': 'vary',
    'samplingProtocolDoc': 'same',
    'samplingProtocolSection': 'same',
    'samplingProtocolVersion': 'same',
    'comments1': 'vary',
    }

    setup = str(setup).replace('\'','"')

    exe_str = f"INSERT INTO user_field_setups (setupName, setup, created) VALUES ('temporary', '{setup}', CURRENT_TIMESTAMP);"
    cur.execute(exe_str)

def create_cruise_tables(DBNAME, METADATA_CATALOGUE, CRUISE_DETAILS_TABLE):
    '''
    Creating the metadata catalogue table within the database to be used for the cruise.

    Creating a table to log the cruise details used for the cruise.

    New tables will be created for each cruise, but within the same database.

    DBNAME: string
        Name of the database within which the tables will be created
    METADATA_CATALOGUE: string
        Name of the table to be created for the metadata catalogue
    CRUISE_DETAILS_TABLE: string
        Name of the table to be created for the cruise details
    '''

    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS hstore;")

    exe_str = f"CREATE TABLE IF NOT EXISTS {METADATA_CATALOGUE} (id uuid PRIMARY KEY, "

    for field in fields.fields:
        if field['hstore'] == False and field['name'] != 'id':
            exe_str = exe_str + field['name'] + " " + field['format'] + ", "

    exe_str = exe_str + "other hstore, metadata hstore)"

    cur.execute(exe_str)

    cur.execute(f'''CREATE TABLE IF NOT EXISTS {CRUISE_DETAILS_TABLE} (id uuid PRIMARY KEY,
    cruise_name text,
    cruise_number integer,
    vessel_name text,
    project text,
    cruise_leader_orcid text,
    cruise_leader_name text,
    cruise_leader_institution text,
    cruise_leader_email text,
    co_cruise_leader_orcid text,
    co_cruise_leader_name text,
    co_cruise_leader_institution text,
    co_cruise_leader_email text,
    comment text,
    created timestamp with time zone)''')

    conn.commit()
    cur.close()
    conn.close()

def run(DBNAME, CRUISE_NUMBER, METADATA_CATALOGUE, CRUISE_DETAILS_TABLE):
    create_database(DBNAME)
    create_cruise_tables(DBNAME, METADATA_CATALOGUE, CRUISE_DETAILS_TABLE)
