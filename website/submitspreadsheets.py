from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
import psycopg2
import psycopg2.extras
import getpass
import uuid
from website.database.get_data import get_data, get_personnel_df
from website.database.input_update_records import insert_into_metadata_catalogue_df, update_record_metadata_catalogue_df
from website.database.harvest_activities import harvest_activities, get_bottom_depth
from website.database.checker import run as checker
import website.database.fields as fields
from website.configurations.get_configurations import get_fields
from website.spreadsheets.make_xlsx import write_file
from website.other_functions.other_functions import distanceCoordinates, split_personnel_list
from . import DBNAME, CRUISE_NUMBER, METADATA_CATALOGUE, CRUISE_DETAILS_TABLE, VESSEL_NAME, TOKTLOGGER
import requests
import numpy as np
from datetime import datetime as dt
import pandas as pd
import os

submitspreadsheets = Blueprint('submitspreadsheets', __name__)

@submitspreadsheets.route('/editActivity/submitSpreadsheet', methods=['GET', 'POST'])
def submit_spreadsheet():
    '''
    Generate template html page code
    '''
    if request.method == 'POST':
          f = request.files['file']
          filepath = '/tmp/'+f.filename
          f.save(filepath)

          errors = []
          good = True

          if filepath.endswith(".xlsx"):
              try:
                  data_df = pd.read_excel(filepath, sheet_name = 'Data', header=2)
              except:
                  errors.append('No sheet named "Data" found. Did you upload the correct file?')
                  good = False
              try:
                  metadata_df = pd.read_excel(filepath, sheet_name = 'Metadata', header=6)
              except:
                  # SHOULD THIS BE COMPULSARY?
                  errors.append('No sheet named "Metadata" found. Did you upload the correct file?')
                  good = False

          else:
              errors.append('File must be an "XLSX" file.')
              good = False

          if good == False:
              for error in errors:
                  flash(error, category='error')

          else:
              new=True
              required_fields_dic, recommended_fields_dic, extra_fields_dic, groups = get_fields(configuration='activity', DBNAME=DBNAME)
              required = list(required_fields_dic.keys())
              recommended = list(recommended_fields_dic.keys())

              # Merging multiple pi details columns and recordedBy details columns
              pi_cols = []
              recordedBy_cols = []
              for col in data_df.columns:
                  if col.startswith('pi_details'):
                      pi_cols.append(col)
                  elif col.startswith('recordedBy_details'):
                      recordedBy_cols.append(col)

              data_df['pi_details'] = data_df[pi_cols].values.tolist()
              data_df['recordedBy_details'] = data_df[recordedBy_cols].values.tolist()

              df_personnel = get_personnel_df(DBNAME=DBNAME, table='personnel')
              data_df[['pi_name','pi_email','pi_institution']] = data_df.apply(lambda row : split_personnel_list(row['pi_details'], df_personnel), axis = 1, result_type = 'expand')
              data_df[['recordedBy_name','recordedBy_email','recordedBy_institution']] = data_df.apply(lambda row : split_personnel_list(row['recordedBy_details'], df_personnel), axis = 1, result_type = 'expand')

              for col in data_df.columns:
                  if col.startswith('pi_details') or col.startswith('recordedBy_details'):
                      data_df.drop(col, axis=1, inplace=True)

              if 'pi_details' in required:
                  required.remove('pi_details')
                  required = required + ['pi_name', 'pi_email', 'pi_institution']
              if 'recordedBy_details' in required:
                  required.remove('recordedBy_details')
                  required = required + ['recordedBy_name', 'recordedBy_email', 'recordedBy_institution']

              good, errors = checker(data_df, required, DBNAME, METADATA_CATALOGUE, new)

              if good == False:
                  for error in errors:
                      flash(error, category='error')
              else:

                  for field in fields.fields:
                      if field['name'] in required or field['name'] in recommended:
                          if field['format'] in ['int', 'double precision', 'time', 'date']:
                              data_df[field['name']] = data_df[field['name']].replace([''], 'NULL')
                              data_df[field['name']].fillna('NULL', inplace=True)
                          elif field['format'] == 'uuid':
                              data_df[field['name']] = data_df[field['name']].replace([''], str(uuid.uuid1()))
                      if field['format'] == 'time' and field['name'] in data_df.columns:
                          data_df[field['name']] = data_df[field['name']].astype('object')
                          data_df[field['name']].fillna('NULL', inplace=True)
                          print(data_df[field['name']])

                  # How should I assign eventids if using spreadsheets?
                  if 'parentID' not in data_df.columns and 'eventID' not in data_df.columns:
                      data_df['eventID'] = data_df['id']
                  elif 'parentID' not in data_df.columns:
                      pass

                  #try:

                  if new == True:

                      data_df['created'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                      data_df['modified'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                      data_df['history'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record uploaded from spreadsheet, filename " + f.filename)
                      data_df['source'] = "Record uploaded from spreadsheet, filename " + f.filename

                      insert_into_metadata_catalogue_df(data_df, DBNAME, METADATA_CATALOGUE)

                      flash('Data from file uploaded successfully!', category='success')

                  else:

                      # These need to be updated to pull multiple values.
                      data_df['history'] = df_metadata_catalogue.loc[df_metadata_catalogue['id'] == eventID, 'history'].iloc[0]
                      data_df['history'] = form_input['history'] + '\n' + dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record modified using edit activity page")
                      data_df['modified'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

                      # Is update working when changing ID? What about fetching above? Need an original ID and new ID variable surely.
                      update_record_metadata_catalogue_df(data_df, DBNAME, METADATA_CATALOGUE)

                      flash('Data from file updated successfully!', category='success')

                  return redirect(url_for('views.home'))

                  #except:
                #      flash('Unexpected fail upon upload. Please check your file and try again, or contact someone for help', category='error')

                      # Unexpected fail error message if above fails?



    return render_template(
    "submitSpreadsheet.html"
    )
