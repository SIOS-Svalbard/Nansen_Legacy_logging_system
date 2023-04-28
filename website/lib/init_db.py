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
import pandas as pd
import json

def create_database(DB):
    '''
    Initialising the database if it doesn't already exist.

    A single database will run on the vessel for all cruises, so that the tables within can be used for future cruises.
    This allows someone to log a station name on one cruise and use it again on the next cruise for example.

    DB: dictionary
        Details of the database to be created
    '''

    DB_WITHOUT_DBNAME = {k: DB[k] for k in DB.keys() if k != "dbname"}
    conn = psycopg2.connect(**DB_WITHOUT_DBNAME)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute('SELECT datname FROM pg_database;')
    list_databases = cur.fetchall()

    # Initialise database if doesn't exist
    if (DB['dbname'],) in list_databases:
        print(f'Database {DB["dbname"]} already exists')
    else:
        print('Creating database...')
        cur.execute(f'CREATE database {DB["dbname"]}')
        cur.close()
        conn.close() # CREATE DATABASE cannot be executed inside a transaction block, so disconnecting and reconnecting

        conn = psycopg2.connect(**DB)
        #conn = psycopg2.connect(dbname=DB["dbname"], user=DB["user"], password=DB["password"])
        cur = conn.cursor()

        # Creating tables and adding some values
        init_institutions(cur)
        init_sample_types(cur)
        init_gear_types(cur)
        init_intended_methods(cur)
        init_projects(cur)
        init_storage_temperatures(cur)
        init_filters(cur)
        init_sex(cur)
        init_kingdoms(cur)
        init_cruises(cur)

        conn.commit()
        cur.close()
        conn.close()

        print(f'Database created with name {DB["dbname"]}')

def init_institutions(cur):
    cur.execute("CREATE TABLE institutions (id uuid PRIMARY KEY, short_name text, full_name text, comment text, created timestamp with time zone)")
    df = pd.read_csv('website/config/dropdown_initial_values/institutions.csv')
    for idx, row in df.iterrows():
        id = row['id']
        short_name = row['short_name']
        full_name = row['full_name']
        comment = row['comment']
        cur.execute(f"INSERT INTO institutions (id, short_name, full_name, comment, created) VALUES ('{id}', '{short_name}', '{full_name}', '{comment}', CURRENT_TIMESTAMP);")

def init_sample_types(cur):
    cur.execute("CREATE TABLE sample_types (id uuid PRIMARY KEY, sampleType text, comment text, grouping text, vocabLabel text, vocabURI text, created timestamp with time zone)")

    df = pd.read_csv('website/Learnings_from_AeN_template_generator/website/config/dropdown_lists/sampleType.csv')

    for idx, row in df.iterrows():
        ID = row['id']
        sampleType = row['sampleType']
        comment = row['comment']
        group = row['group']
        vocabLabel = row['vocabLabel']
        vocabURI = row['vocabURI']
        cur.execute(f"INSERT INTO sample_types (id, sampleType, comment, grouping, vocabLabel, vocabURI, created) VALUES ('{ID}','{sampleType}','{comment}','{group}','{vocabLabel}','{vocabURI}', CURRENT_TIMESTAMP);")

def init_gear_types(cur):
    cur.execute("CREATE TABLE gear_types (id uuid PRIMARY KEY, gearType text, IMR_name text, comment text, grouping text, vocabLabel text, vocabURI text, recommendedSampleTypes text, recommendedChildSamples text, created timestamp with time zone)")

    df = pd.read_csv('website/Learnings_from_AeN_template_generator/website/config/dropdown_lists/gearType.csv')

    for idx, row in df.iterrows():
        ID = row['id']
        gearType = row['gearType']
        IMR_name = row['IMR_name']
        comment = row['comment']
        group = row['group']
        vocabLabel = row['vocabLabel']
        vocabURI = row['vocabURI']
        recommendedSampleTypes = row['recommendedSampleTypes']
        recommendedChildSamples = row['recommendedChildren']

        cur.execute(f"INSERT INTO gear_types (id, gearType, IMR_name, comment, grouping, vocabLabel, vocabURI, recommendedSampleTypes, recommendedChildSamples, created) VALUES ('{ID}','{gearType}','{IMR_name}','{comment}','{group}','{vocabLabel}','{vocabURI}','{recommendedSampleTypes}','{recommendedChildSamples}', CURRENT_TIMESTAMP);")

def init_intended_methods(cur):
    cur.execute("CREATE TABLE intended_methods (id uuid PRIMARY KEY, intendedMethod text, comment text, created timestamp with time zone)")
    df = pd.read_csv('website/Learnings_from_AeN_template_generator/website/config/dropdown_lists/intendedMethod.csv')
    for idx, row in df.iterrows():
        id = row['id']
        intendedMethod = row['intendedMethod']
        comment = row['comment']
        cur.execute(f"INSERT INTO intended_methods (id, intendedMethod, comment, created) VALUES ('{id}', '{intendedMethod}', '{comment}', CURRENT_TIMESTAMP);")

def init_projects(cur):
    cur.execute("CREATE TABLE projects (id uuid PRIMARY KEY, project text, comment text, created timestamp with time zone)")
    df = pd.read_csv('website/config/dropdown_initial_values/projects.csv')
    for idx, row in df.iterrows():
        id = row['id']
        project = row['project']
        comment = row['comment']
        cur.execute(f"INSERT INTO projects (id, project, comment, created) VALUES ('{id}', '{project}', '{comment}', CURRENT_TIMESTAMP);")

def init_storage_temperatures(cur):
    cur.execute("CREATE TABLE storage_temperatures (id uuid PRIMARY KEY, storageTemp text, comment text, created timestamp with time zone)")
    df = pd.read_csv('website/Learnings_from_AeN_template_generator/website/config/dropdown_lists/storageTemp.csv')
    for idx, row in df.iterrows():
        id = row['id']
        storageTemp = row['storageTemp']
        comment = row['comment']
        cur.execute(f"INSERT INTO storage_temperatures (id, storageTemp, comment, created) VALUES ('{id}', '{storageTemp}','{comment}', CURRENT_TIMESTAMP);")

def init_filters(cur):
    cur.execute("CREATE TABLE filters (id uuid PRIMARY KEY, filter text, comment text, created timestamp with time zone)")
    df = pd.read_csv('website/Learnings_from_AeN_template_generator/website/config/dropdown_lists/filter.csv')
    for idx, row in df.iterrows():
        id = row['id']
        filter = row['filter']
        comment = row['comment']
        cur.execute(f"INSERT INTO filters (id, filter, comment, created) VALUES ('{id}','{filter}','{comment}', CURRENT_TIMESTAMP);")

def init_sex(cur):
    cur.execute("CREATE TABLE sex (id uuid PRIMARY KEY, sex text, comment text, created timestamp with time zone)")
    df = pd.read_csv('website/Learnings_from_AeN_template_generator/website/config/dropdown_lists/sex.csv')
    for idx, row in df.iterrows():
        id = row['id']
        sex = row['sex']
        comment = row['comment']
        cur.execute(f"INSERT INTO sex (id, sex, comment, created) VALUES ('{id}', '{sex}' ,'{comment}', CURRENT_TIMESTAMP);")

def init_kingdoms(cur):
    cur.execute("CREATE TABLE kingdoms (id uuid PRIMARY KEY, kingdom text, comment text, created timestamp with time zone)") # WHAT ABOUT OTHER CLASSIFICATIONS IN SPECIES?
    df = pd.read_csv('website/Learnings_from_AeN_template_generator/website/config/dropdown_lists/kingdom.csv')
    for idx, row in df.iterrows():
        id = row['id']
        kingdom = row['kingdom']
        comment = row['comment']
        cur.execute(f"INSERT INTO kingdoms (id, kingdom, comment, created) VALUES ('{id}', '{kingdom}', '{comment}', CURRENT_TIMESTAMP);")

def init_cruises(cur):
    '''
    Creating a table to log the cruise details used for each cruise.
    '''
    cur.execute(f'''CREATE TABLE IF NOT EXISTS cruises (id uuid PRIMARY KEY,
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
    current boolean,
    comment text,
    created timestamp with time zone)''')

def run(DB):
    '''
    Creating the database and tables.

    DBNAME: string
        Name of the database within which the tables will be createde

    '''
    create_database(DB)
