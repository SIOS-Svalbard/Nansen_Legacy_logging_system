from flask import Blueprint, render_template, request, flash, redirect, url_for
import uuid
from website.lib.get_data import get_data, get_cruise, get_personnel_df, get_subconfig_for_sampletype
from website.lib.input_update_records import insert_into_metadata_catalogue, update_record_metadata_catalogue
from website.lib.checker import run as checker
from website.lib.other_functions import split_personnel_list
from website import DB, METADATA_CATALOGUE, FIELDS_FILEPATH
from datetime import datetime as dt
import pandas as pd
import numpy as np
from website.lib.get_setup_for_configuration import get_setup_for_configuration

def group_rows(numbers):
    groups = []
    start = None
    end = None

    for num in numbers:
        if start is None:
            start = num
            end = num
        elif num == end + 1:
            end = num
        else:
            if start == end:
                groups.append(str(start))
            else:
                groups.append(f"{start}-{end}")
            start = num
            end = num

    if start is not None:
        if start == end:
            groups.append(str(start))
        else:
            groups.append(f"{start}-{end}")

    return ', '.join(groups)

def prepare_and_check(data_df, subconfig, CRUISE_NUMBER, header_row):

    df_subconfig = data_df.loc[data_df['subconfig'] == subconfig]

    # 3. Get setup for subconfiguration and check all dfs based on subconfiguration
    (
        output_config_dict,
        output_config_fields,
        extra_fields_dict,
        cf_standard_names,
        dwc_terms,
        dwc_terms_not_in_config,
        all_fields_dict,
        added_fields_dic,
        added_cf_names_dic,
        added_dwc_terms_dic,
        groups
    ) = get_setup_for_configuration(
        fields_filepath=FIELDS_FILEPATH,
        subconfig=subconfig,
        CRUISE_NUMBER=CRUISE_NUMBER
    )

    required = list(output_config_dict['Data']['Required'].keys())

    if 'pi_details' in required:
        required.remove('pi_details')
        required = required + ['pi_name', 'pi_email', 'pi_institution']
    if 'recordedBy' in required:
        required.remove('recordedBy')
        required = required + ['recordedBy_name', 'recordedBy_email', 'recordedBy_institution']

    df_subconfig.drop('subconfig', axis=1, inplace=True)

    if 'id' not in df_subconfig.columns:
        df_subconfig['id'] = [str(uuid.uuid4()) for ii in range(len(df_subconfig))]
    else:
        df_subconfig['id'] = df_subconfig['id'].apply(lambda x: str(uuid.uuid4()) if x == '' else x)

    firstrow = header_row + 2
    good, errors = checker(
        data=df_subconfig,
        required=required,
        DB=DB,
        CRUISE_NUMBER=CRUISE_NUMBER,
        new=True,
        firstrow = firstrow
        )
    # Is checker checking PI and recordedBy properly?

    rows = df_subconfig.index.values.tolist()
    rows = [row + firstrow for row in rows]

    # Grouping errors
    # A: Required fields missing
    missing_fields = []
    other_errors = []
    for error in errors:
        if 'Required field' in error and 'is missing' in error:
            missing_field = error.split('"')[1]
            missing_fields.append(missing_field)
        else:
            other_errors.append(error)
    errors = other_errors
    missing_field_rows = group_rows(rows)

    if len(missing_fields) > 0:
        errors.append(f"Required fields missing for rows {missing_field_rows}:<br> {missing_fields}<br>Could alternatively be that 'sampleType' has not been provided, so this has been assumed to be an activity")

    if good == False:
        for error in errors:
            flash(f"{error}", category='error')
            # OR WHERE THERE IS NO SAMPLE TYPE
            # GROUP TOGETHER THE ERRORS HERE FOR REQUIRED FIELDS MISSING
            # SOMEHOW BREAK DOWN BY SUBCONFIG, AND STATE WHICH SAMPLES TYPES FALL WITHIN THIS
    else:
        flash(f'No errors for row(s): {missing_field_rows}', category='success')

    return df_subconfig

uploaddata = Blueprint('uploaddata', __name__)

@uploaddata.route('/uploadData', methods=['GET', 'POST'])
def upload_data():
    '''
    Upload data logged in Excel templates
    '''
    if request.method == 'POST':

        cruise_details_df = get_cruise(DB)
        CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

        f = request.files['file']

        if f.filename == '':
            flash('No file selected', category='error')

        else:

            filepath = '/tmp/'+f.filename
            f.save(filepath)

            errors = []
            warnings = []
            good = True
            header_row = 9 # Hidden row on row 10

            if filepath.endswith(".xlsx"):
                try:
                    data_df = pd.read_excel(filepath, sheet_name = 'Data', header=header_row)
                except:
                    errors.append("Data couldn't be read from the Data sheet. Did you upload the correct file? The column headers should be on hidden row 10.")
                    good = False
                try:
                    metadata_df = pd.read_excel(filepath, sheet_name = 'Metadata', header=6, usecols='B:C', index_col=0)
                    metadata_df = metadata_df.transpose()
                    metadata_df.fillna('NULL', inplace=True)
                except:
                    metadata_df = None
                    warnings.append("Data couldn't be read from the Metadata sheet. Uploading the records from the Data sheet without it.")

            else:
                errors.append('File must be an "XLSX" file.')
                good = False

            if warnings != []:
                for warning in warnings:
                    flash(warning, category='warning')
            if good == False:
                for error in errors:
                    flash(error, category='error')

            else:
                if request.form['submitbutton'] == 'new':
                    new = True
                elif request.form['submitbutton'] == 'update':
                    new = False

                # Merging multiple pi details columns and recordedBy details columns
                pi_cols = []
                recordedBy_cols = []
                for col in data_df.columns:
                    if col.startswith('pi_details'):
                        pi_cols.append(col)
                    elif col.startswith('recordedBy') and col not in ['recordedBy_name','recordedBy_email','recordedBy_institution','recordedBy_orcid']:
                        recordedBy_cols.append(col)

                if len(pi_cols) + len(recordedBy_cols) > 0:
                    df_personnel = get_personnel_df(DB=DB, table='personnel', CRUISE_NUMBER=CRUISE_NUMBER)

                if len(pi_cols) > 0:
                    data_df['pi_details'] = data_df[pi_cols].values.tolist()
                    data_df[['pi_name','pi_email','pi_orcid', 'pi_institution']] = data_df.apply(lambda row : split_personnel_list(row['pi_details'], df_personnel), axis = 1, result_type = 'expand')
                    for col in data_df.columns:
                        if col.startswith('pi_details'):
                            data_df.drop(col, axis=1, inplace=True)
                if len(recordedBy_cols) > 0:
                    data_df['recordedBy'] = data_df[recordedBy_cols].values.tolist()
                    data_df[['recordedBy_name','recordedBy_email','recordedBy_orcid','recordedBy_institution']] = data_df.apply(lambda row : split_personnel_list(row['recordedBy'], df_personnel), axis = 1, result_type = 'expand')
                    for col in data_df.columns:
                        if col.startswith('recordedBy') and col not in ['recordedBy_name','recordedBy_email','recordedBy_institution','recordedBy_orcid']:
                            data_df.drop(col, axis=1, inplace=True)

                # 1. Divide df based on subconfig
                data_df['subconfig'] = ''
                if 'sampleType' in data_df.columns:
                    sampleTypes = list(set(data_df['sampleType']))
                    # 2. Get subconfiguration for sampleType. If no sampleType and no parent, assume it is an activity (top of pyramid).
                    for sampleType in sampleTypes:
                        subconfig = get_subconfig_for_sampletype(sampleType, DB)
                        data_df.loc[data_df['sampleType'] == sampleType, 'subconfig'] = data_df.loc[data_df['sampleType'] == sampleType, 'subconfig'].apply(lambda x: subconfig if x == '' else x)
                    data_df.loc[data_df['sampleType'].isna(), 'subconfig'] = 'Activities'

                    subconfigs_included = list(set(data_df['subconfig']))

                    for subconfig in subconfigs_included:

                        df_subconfig = prepare_and_check(data_df, subconfig, CRUISE_NUMBER, header_row)

                    for subconfig in subconfigs_included:
                        if subconfig == 'Niskin bottles':
                            df_subconfig['eventID'] = df_subconfig['id']
                        # 4. Only upload records once checker passed for all dfs (the whole sheet)

                        # Need to reassign personnel details based on email address and content of df_personnel
                        # This is because someone might enter a different version of the name and we need consistency.
                else:
                    subconfig = 'Activities'
                    data_df['subconfig'] = subconfig
                    df_subconfig = prepare_and_check(data_df, subconfig, CRUISE_NUMBER, header_row)
                    df_subconfig['eventID'] = df_subconfig['id']






                #
                #     try:
                #
                #         if new == True:
                #
                #             data_df['created'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                #             data_df['modified'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                #             data_df['history'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record uploaded from spreadsheet, filename " + f.filename)
                #             data_df['source'] = "Record uploaded from spreadsheet, filename " + f.filename
                #
                #             insert_into_metadata_catalogue_df(data_df, metadata_df, DB, METADATA_CATALOGUE)
                #
                #             flash('Data from file uploaded successfully!', category='success')
                #
                #         else:
                #
                #             df_metadata_catalogue = get_data(DB, METADATA_CATALOGUE)
                #             ids = list(data_df['id'])
                #             data_df['history'] = df_metadata_catalogue.loc[df_metadata_catalogue['id'].isin(ids), 'history'].iloc[0]
                #             data_df['history'] = data_df['history'] + '\n' + dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ New version submitted from spreadsheet, source filename " + f.filename)
                #             data_df['modified'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                #             update_record_metadata_catalogue_df(data_df, metadata_df, DB, METADATA_CATALOGUE)
                #
                #             [flash(f'Record with ID {id} not registered in metadata catalogue so will be ignored', category='warning') for id in ids if id not in df_metadata_catalogue['id'].values]
                #
                #             flash('Data from file updated successfully!', category='success')
                #
                #             return redirect(url_for('views.home'))
                #
                #     except:
                #         flash('Unexpected fail upon upload. Please check your file and try again, or contact someone for help', category='error')

    return render_template(
    "submitSpreadsheet.html"
    )
