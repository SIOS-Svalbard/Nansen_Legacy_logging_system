from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
import psycopg2
import psycopg2.extras
import getpass
import uuid
from website.database.get_data import get_data, get_cruise, get_user_setup, get_metadata_for_id, get_personnel_df
from website.database.propegate_parents_to_children import propegate_parents_to_children
from website.database.input_update_records import insert_into_metadata_catalogue_df, update_record_metadata_catalogue_df
from website.database.harvest_activities import harvest_activities, get_bottom_depth
from website.database.checker import run as checker
import website.database.fields as fields
from website.configurations.get_configurations import get_fields
from website.spreadsheets.make_xlsx import write_file
from website.other_functions.other_functions import distanceCoordinates, split_personnel_list, combine_personnel_details
from . import DB, CRUISE_NUMBER, METADATA_CATALOGUE, VESSEL_NAME, TOKTLOGGER
import requests
import numpy as np
from datetime import datetime as dt
import pandas as pd
import os
import yaml

logsamplesform = Blueprint('logsamplesform', __name__)

@logsamplesform.route('/logSamples/parentid=<parentID>/form/sampletype=<sampleType>&num=<num_samples>&setup=<current_setup>', methods=['GET', 'POST'])
def log_samples_form(parentID,sampleType,num_samples,current_setup):
    '''
    Generate template html page code
    '''

    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

    setups = yaml.safe_load(open(os.path.join("website/configurations", "template_configurations.yaml"), encoding='utf-8'))['setups']

    config = 'default'
    for setup in setups:
        if setup['name'] == sampleType:
            config = sampleType

    required_fields_dic, recommended_fields_dic, extra_fields_dic, groups = get_fields(configuration=config, DB=DB, CRUISE_NUMBER=CRUISE_NUMBER)
    all_fields_dic = {**required_fields_dic, **recommended_fields_dic, **extra_fields_dic}

    required = list(required_fields_dic.keys())
    added_fields_dic = {}

    userSetup = get_user_setup(DB, CRUISE_NUMBER, current_setup) # json of setup

    # adding data for fields in setup to dictionaries to be displayed through HTML
    for key, val in userSetup.items():
        if '|' in val:
            checked = val.split(' | ')
        else:
            checked = [val]

        if key in required:
            required_fields_dic[key]['checked'] = checked
        if key in recommended_fields_dic.keys():
            recommended_fields_dic[key]['checked'] = checked
        if key in extra_fields_dic.keys():
            for field in fields.fields:
                if field['name'] == key:
                    added_fields_dic[key] = {}
                    added_fields_dic[key]['disp_name'] = field['disp_name']
                    added_fields_dic[key]['description'] = field['description']
                    added_fields_dic[key]['checked'] = checked

    # Removing recommended fields that aren't included in user setup.
    rem_list = []
    for key, val in recommended_fields_dic.items():
        if key not in userSetup.keys():
            rem_list.append(key)
    for key in rem_list:
        del recommended_fields_dic[key]

    # Combining dictionaries
    for key, val in required_fields_dic.items():
        val['requirements'] = 'required'
    for key, val in recommended_fields_dic.items():
        val['requirements'] = 'recommended'
    for key, val in added_fields_dic.items():
        val['requirements'] = 'optional'

    setup_fields_dic = {**required_fields_dic, **recommended_fields_dic, **added_fields_dic}

    if len(added_fields_dic) > 0:
        added_fields_bool = True
    else:
        added_fields_bool = False

    gear_list = all_fields_dic['gearType']['source']
    if sampleType in gear_list:
        gearType = sampleType
    else:
        gearType = None

    for key, val in setup_fields_dic.items():

        if userSetup[key] == 'same':
            if key == 'sampleType':
                val['values'] = sampleType
            elif key == 'gearType':
                val['values'] = gearType
            else:
                val['values'] = ''
        elif userSetup[key] == 'vary':
            if key == 'sampleType':
                val['values'] = [sampleType] * int(num_samples)
            elif key == 'gearType':
                val['values'] = [gearType] * int(num_samples)
            else:
                val['values'] = [''] * int(num_samples)

    parent_df = get_metadata_for_id(DB, CRUISE_NUMBER, parentID)
    parent_details = {}

    parent_fields = [
    'id',
    'gearType',
    'sampleType',
    'stationName',
    'decimalLatitude',
    'decimalLongitude',
    'eventDate',
    'eventTime',
    'minimumDepthInMeters',
    'maximumDepthInMeters'
    ]

    for parent_field in parent_fields:
        parent_details[parent_field] = all_fields_dic[parent_field]
        parent_details[parent_field]['value'] = parent_df[parent_field.lower()][0]

    if request.method == 'POST':

        form_input = request.form.to_dict(flat=False)

        df_personnel = get_personnel_df(DB=DB, CRUISE_NUMBER=CRUISE_NUMBER, table='personnel')

        cols = userSetup.keys()

        # Initialising dataframe
        df_to_submit = pd.DataFrame(columns = cols, index=np.arange(int(num_samples)))

        df_to_submit['parentID'] = parentID
        fields_to_submit = []
        rows = list(range(int(num_samples)))

        for key, value in form_input.items():

            if '|' not in key and key not in ['submit','labelType', 'movefieldtovary', 'movefieldtosame']:
                fields_to_submit.append(key)
                if key in ['pi_details','recordedBy_details']:
                    df_to_submit[key] = ' | '.join(value)
                    setup_fields_dic[key]['values'] = ' | '.join(value)
                else:
                    df_to_submit[key] = value[0]
                    setup_fields_dic[key]['values'] = value[0]

            if '|' in key and value != ['']:
                field, row = key.split('|')
                fields_to_submit.append(field)
                row = int(row)

                if row in rows:
                    if len(value) == 1 and field not in ['pi_details', 'recordedBy_details']:
                        df_to_submit[field][row] = value[0]
                        setup_fields_dic[field]['values'][row] = value[0]
                    elif field in ['pi_details','recordedBy_details']:
                        df_to_submit[field][row] = ' | '.join(value)
                        setup_fields_dic[field]['values'][row] = value
                    elif len(value) == 0:
                        df_to_submit[field][row] = ''
                        setup_fields_dic[field]['values'][row] = ''

        if 'movefieldtovary' in form_input.keys():
            fieldtovary = form_input['movefieldtovary'][0]
            userSetup[fieldtovary] = 'vary'

            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            userSetup = str(userSetup).replace('\'','"')

            exe_str = f"UPDATE user_field_setups SET setup = '{str(userSetup)}', created = CURRENT_TIMESTAMP WHERE setupName = 'temporary';"

            cur.execute(exe_str)
            conn.commit()
            cur.close()
            conn.close()

            return redirect(f'/logSamples/parentid={parentID}/form/sampletype={sampleType}&num={num_samples}&setup=temporary')

        elif 'movefieldtosame' in form_input.keys():
            fieldtovary = form_input['movefieldtosame'][0]
            userSetup[fieldtovary] = 'same'

            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            userSetup = str(userSetup).replace('\'','"')

            exe_str = f"UPDATE user_field_setups SET setup = '{str(userSetup)}', created = CURRENT_TIMESTAMP WHERE setupName = 'temporary';"

            cur.execute(exe_str)
            conn.commit()
            cur.close()
            conn.close()

            return redirect(f'/logSamples/parentid={parentID}/form/sampletype={sampleType}&num={num_samples}&setup=temporary')

        elif 'submit' in form_input.keys():

            if form_input['submit'] != ['printLabels']:
                form_input.pop('labelType')

            if form_input['submit'] == ['submitForm']:

                if 'pi_details' in fields_to_submit:
                    df_to_submit[['pi_name','pi_email','pi_orcid','pi_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['pi_details'], df_personnel), axis = 1, result_type = 'expand')
                    fields_to_submit.remove('pi_details')
                    fields_to_submit = fields_to_submit + ['pi_name', 'pi_email', 'pi_orcid', 'pi_institution']
                if 'recordedBy_details' in fields_to_submit:
                    df_to_submit[['recordedBy_name','recordedBy_email','recordedBy_orcid','recordedBy_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['recordedBy_details'], df_personnel), axis = 1, result_type = 'expand')
                    fields_to_submit.remove('recordedBy_details')
                    fields_to_submit = fields_to_submit + ['recordedBy_name', 'recordedBy_email', 'recordedBy_orcid', 'recordedBy_institution']

                fields_to_submit = fields_to_submit + ['parentID']

                if 'pi_details' in required:
                    df_to_submit[['pi_name','pi_email','pi_orcid','pi_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['pi_details'], df_personnel), axis = 1, result_type = 'expand')
                    required.remove('pi_details')
                    required = required + ['pi_name', 'pi_email', 'pi_orcid', 'pi_institution']
                if 'recordedBy_details' in required:
                    df_to_submit[['recordedBy_name','recordedBy_email','recordedBy_orcid','recordedBy_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['recordedBy_details'], df_personnel), axis = 1, result_type = 'expand')
                    required.remove('recordedBy_details')
                    required = required + ['recordedBy_name', 'recordedBy_email', 'recordedBy_orcid', 'recordedBy_institution']

                required = required + ['parentID']

                for col in df_to_submit.columns:
                    if col not in fields_to_submit and col != 'id':
                        df_to_submit.drop(col, axis=1, inplace=True)

                metadata_df = False

                if 'id' not in df_to_submit.columns:
                    df_to_submit['id'] = [str(uuid.uuid1()) for ii in range(len(df_to_submit))]

                good, errors = checker(
                    data=df_to_submit,
                    required=required,
                    DB=DB,
                    CRUISE_NUMBER=CRUISE_NUMBER,
                    new=True
                    )

                if good == False:
                    for error in errors:
                        flash(error, category='error')

                else:

                    df_to_submit = propegate_parents_to_children(df_to_submit,DB, CRUISE_NUMBER)

                    for field in fields.fields:
                        if field['name'] in df_to_submit.columns:
                            if field['format'] in ['int', 'double precision', 'time', 'date']:
                                df_to_submit[field['name']] = df_to_submit[field['name']].replace('', 'NULL')
                                df_to_submit[field['name']].fillna('NULL', inplace=True)
                            elif field['name'] == 'id':
                                df_to_submit[field['name']].fillna('', inplace=True)
                                for idx, row in df_to_submit.iterrows():
                                    if row[field['name']] == '':
                                        df_to_submit[field['name']][idx] = str(uuid.uuid1())
                        if field['format'] == 'time' and field['name'] in df_to_submit.columns:
                            df_to_submit[field['name']] = df_to_submit[field['name']].astype('object')
                            df_to_submit[field['name']].fillna('NULL', inplace=True)

                    df_to_submit['created'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                    df_to_submit['modified'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                    df_to_submit['history'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record uploaded from GUI form")
                    df_to_submit['source'] = "Record uploaded from GUI form"

                    insert_into_metadata_catalogue_df(df_to_submit, metadata_df, DB, CRUISE_NUMBER)

                    flash('Data from file uploaded successfully!', category='success')

                    return redirect(f'/logSamples/parentid={parentID}')

            elif form_input['submit'] == ['generateExcel']:

                filepath = f'/tmp/{CRUISE_NUMBER}_{sampleType}_parent{parentID}.xlsx'

                df_to_submit.fillna('', inplace=True)
                write_file(filepath, df_to_submit.columns, metadata=True, conversions=True, data=df_to_submit, metadata_df=False, DB=DB, CRUISE_NUMBER=CRUISE_NUMBER)

                return send_file(filepath, as_attachment=True)

            elif form_input['submit'] == ['submitExcel']:

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
                            df_to_submit = pd.read_excel(filepath, sheet_name = 'Data', header=2)
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
                        new=True

                        # Merging multiple pi details columns and recordedBy details columns
                        pi_cols = []
                        recordedBy_cols = []
                        for col in df_to_submit.columns:
                            if col.startswith('pi_details'):
                                pi_cols.append(col)
                            elif col.startswith('recordedBy_details'):
                                recordedBy_cols.append(col)

                        df_to_submit['pi_details'] = df_to_submit[pi_cols].values.tolist()
                        df_to_submit['recordedBy_details'] = df_to_submit[recordedBy_cols].values.tolist()

                        df_personnel = get_personnel_df(DB=DB, table='personnel')
                        df_to_submit[['pi_name','pi_email','pi_orcid', 'pi_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['pi_details'], df_personnel), axis = 1, result_type = 'expand')
                        df_to_submit[['recordedBy_name','recordedBy_email','recordedBy_orcid','recordedBy_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['recordedBy_details'], df_personnel), axis = 1, result_type = 'expand')

                        for col in df_to_submit.columns:
                            if col.startswith('pi_details') or col.startswith('recordedBy_details'):
                                df_to_submit.drop(col, axis=1, inplace=True)

                        if 'pi_details' in required:
                            required.remove('pi_details')
                            required = required + ['pi_name', 'pi_email', 'pi_orcid', 'pi_institution']
                        if 'recordedBy_details' in required:
                            required.remove('recordedBy_details')
                            required = required + ['recordedBy_name', 'recordedBy_email', 'recordedBy_orcid', 'recordedBy_institution']

                        good, errors = checker(
                            data=df_to_submit,
                            metadata=metadata_df,
                            required=required,
                            DB=DB,
                            CRUISE_NUMBER=CRUISE_NUMBER,
                            new=new,
                            firstrow=4
                            )

                        if good == False:
                            for error in errors:
                                flash(error, category='error')
                        else:

                            df_to_submit = propegate_parents_to_children(df_to_submit,DB, CRUISE_NUMBER)
                            # How should I assign eventids if using spreadsheets?

                            # Write to function? Used multiple times
                            for field in fields.fields:
                                if field['name'] in df_to_submit.columns:
                                    if field['format'] in ['int', 'double precision', 'time', 'date']:
                                        df_to_submit[field['name']] = df_to_submit[field['name']].replace([''], 'NULL')
                                        df_to_submit[field['name']].fillna('NULL', inplace=True)
                                    elif field['name'] == 'id':
                                        df_to_submit[field['name']].fillna('', inplace=True)
                                        for idx, row in df_to_submit.iterrows():
                                            if row[field['name']] == '':
                                                df_to_submit[field['name']][idx] = str(uuid.uuid1())
                                    else:
                                        df_to_submit[field['name']].fillna('', inplace=True)
                                if field['format'] == 'time' and field['name'] in df_to_submit.columns:
                                    df_to_submit[field['name']] = df_to_submit[field['name']].astype('object')
                                    df_to_submit[field['name']].fillna('NULL', inplace=True)
                            try:

                                df_to_submit['created'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                                df_to_submit['modified'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                                df_to_submit['history'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record uploaded from spreadsheet, filename " + f.filename)
                                df_to_submit['source'] = "Record uploaded from spreadsheet, filename " + f.filename

                                insert_into_metadata_catalogue_df(df_to_submit, metadata_df, DB, CRUISE_NUMBER)

                                flash('Data from file uploaded successfully!', category='success')
                                return redirect(f'/logSamples/parentid={parentID}')

                            except:
                                flash('Unexpected fail upon upload. Please check your file and try again, or contact someone for help', category='error')

    return render_template(
    "logSamplesForm.html",
    parentID=parentID,
    parent_details=parent_details,
    sampleType=sampleType,
    gearType=gearType,
    setup_fields_dic = setup_fields_dic,
    extra_fields_dic = extra_fields_dic,
    groups = groups,
    num_rows = int(num_samples)
    )
