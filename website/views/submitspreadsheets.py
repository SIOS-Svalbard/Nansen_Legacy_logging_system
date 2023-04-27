from flask import Blueprint, render_template, request, flash, redirect, url_for
import uuid
from website.lib.get_data import get_data, get_personnel_df
from website.lib.input_update_records import insert_into_metadata_catalogue_df, update_record_metadata_catalogue_df
from website.lib.checker import run as checker
from website.lib.other_functions import split_personnel_list
from . import DB, METADATA_CATALOGUE
from datetime import datetime as dt
import pandas as pd

submitspreadsheets = Blueprint('submitspreadsheets', __name__)

@submitspreadsheets.route('/editActivity/submitSpreadsheet', methods=['GET', 'POST'])
def submit_spreadsheet():
    '''
    Generate template html page code
    '''
    if request.method == 'POST':

        f = request.files['file']

        if f.filename == '':
            flash('No file selected', category='error')

        else:

            filepath = '/tmp/'+f.filename
            f.save(filepath)

            errors = []
            warnings = []
            good = True

            if filepath.endswith(".xlsx"):
                try:
                    data_df = pd.read_excel(filepath, sheet_name = 'Data', header=2)
                except:
                    errors.append('No sheet named "Data" found. Did you upload the correct file?')
                    good = False
                try:
                    metadata_df = pd.read_excel(filepath, sheet_name = 'Metadata', header=6, usecols='B:C', index_col=0)
                    metadata_df = metadata_df.transpose()
                    metadata_df.fillna('NULL', inplace=True)
                except:
                    metadata_df = False
                    warnings.append('No sheet named "Metadata" found. Uploading the data without it.')

            else:
                errors.append('File must be an "XLSX" file.')
                good = False

            if good == False:
                for error in errors:
                    flash(error, category='error')
            if warnings != []:
                for warning in warnings:
                    flash(warning, category='warning')

            else:
                if request.form['submitbutton'] == 'new':
                    new = True
                elif request.form['submitbutton'] == 'update':
                    new = False

                required_fields_dic, recommended_fields_dic, extra_fields_dic, groups = get_fields(configuration='activity', DB=DB)
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

                df_personnel = get_personnel_df(DB=DB, table='personnel')
                data_df[['pi_name','pi_email','pi_orcid', 'pi_institution']] = data_df.apply(lambda row : split_personnel_list(row['pi_details'], df_personnel), axis = 1, result_type = 'expand')
                data_df[['recordedBy_name','recordedBy_email','recordedBy_orcid','recordedBy_institution']] = data_df.apply(lambda row : split_personnel_list(row['recordedBy_details'], df_personnel), axis = 1, result_type = 'expand')

                for col in data_df.columns:
                    if col.startswith('pi_details') or col.startswith('recordedBy_details'):
                        data_df.drop(col, axis=1, inplace=True)

                if 'pi_details' in required:
                    required.remove('pi_details')
                    required = required + ['pi_name', 'pi_email', 'pi_orcid', 'pi_institution']
                if 'recordedBy_details' in required:
                    required.remove('recordedBy_details')
                    required = required + ['recordedBy_name', 'recordedBy_email', 'recordedBy_orcid', 'recordedBy_institution']

                good, errors = checker(
                    data=data_df,
                    metadata=metadata_df,
                    required=required,
                    DB=DB,
                    METADATA_CATALOGUE=METADATA_CATALOGUE,
                    new=new,
                    firstrow=4
                    )

                if good == False:
                    for error in errors:
                        flash(error, category='error')
                else:

                    for field in fields.fields:
                        if field['name'] in data_df.columns:
                            if field['format'] in ['int', 'double precision', 'time', 'date']:
                                data_df[field['name']] = data_df[field['name']].replace('', 'NULL')
                                data_df[field['name']].fillna('NULL', inplace=True)
                            elif field['name'] == 'id':
                                data_df[field['name']].fillna('', inplace=True)
                                for idx, row in data_df.iterrows():
                                    if row[field['name']] == '':
                                        data_df[field['name']][idx] = str(uuid.uuid1())
                        if field['format'] == 'time' and field['name'] in data_df.columns:
                            data_df[field['name']] = data_df[field['name']].astype('object')
                            data_df[field['name']].fillna('NULL', inplace=True)

                    # How should I assign eventids if using spreadsheets?
                    if 'parentID' not in data_df.columns and 'eventID' not in data_df.columns:
                        data_df['eventID'] = data_df['id']
                    elif 'parentID' not in data_df.columns:
                        pass

                    try:

                        if new == True:

                            data_df['created'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                            data_df['modified'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                            data_df['history'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record uploaded from spreadsheet, filename " + f.filename)
                            data_df['source'] = "Record uploaded from spreadsheet, filename " + f.filename

                            insert_into_metadata_catalogue_df(data_df, metadata_df, DB, METADATA_CATALOGUE)

                            flash('Data from file uploaded successfully!', category='success')

                        else:

                            df_metadata_catalogue = get_data(DB, METADATA_CATALOGUE)
                            ids = list(data_df['id'])
                            data_df['history'] = df_metadata_catalogue.loc[df_metadata_catalogue['id'].isin(ids), 'history'].iloc[0]
                            data_df['history'] = data_df['history'] + '\n' + dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ New version submitted from spreadsheet, source filename " + f.filename)
                            data_df['modified'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                            update_record_metadata_catalogue_df(data_df, metadata_df, DB, METADATA_CATALOGUE)

                            [flash(f'Record with ID {id} not registered in metadata catalogue so will be ignored', category='warning') for id in ids if id not in df_metadata_catalogue['id'].values]

                            flash('Data from file updated successfully!', category='success')

                            return redirect(url_for('views.home'))

                    except:
                        flash('Unexpected fail upon upload. Please check your file and try again, or contact someone for help', category='error')

    return render_template(
    "submitSpreadsheet.html"
    )
