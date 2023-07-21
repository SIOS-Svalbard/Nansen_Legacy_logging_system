from flask import Blueprint, render_template, request, flash, redirect, url_for
import uuid
from website.lib.get_data import get_data, get_cruise, get_personnel_df, get_subconfig_for_sampletype, get_all_sources
from website.lib.input_update_records import insert_into_metadata_catalogue, update_record_metadata_catalogue
from website.lib.checker import run as checker
from website.lib.other_functions import split_personnel_list, format_form_value
from website import DB, METADATA_CATALOGUE, FIELDS_FILEPATH, CONFIG
from datetime import datetime as dt
import pandas as pd
import numpy as np
from website.lib.get_setup_for_configuration import get_setup_for_configuration
from website.lib.propegate_parents_to_children import propegate_parents_to_children, propegate_update_to_children
from website.lib.get_dict_for_list_of_fields import get_dict_for_list_of_fields
from website.lib.get_data import get_metadata_for_list_of_ids

def reassign_personnel_based_on_email(data_df, df_personnel):
    '''
    Reassigning personnel name, institution and OrcID (if registered) based on email
    This is because when uploading from a spreadsheet, someone might use a different version/spelling
    of a name or institution

    data_df: Pandas dataframe
    The dataframe including the records to upload

    df_personnel: Pandas dataframe
    The dataframe including details of all the personnel registered in the system
    '''
    if 'recordedBy_email' in data_df.columns:
        if 'recordedBy_name' in data_df.columns:
            data_df['recordedBy_name'] = data_df.apply(lambda row : get_personnel_details_from_email(row['recordedBy_email'], 'name', df_personnel, row['recordedBy_name']), axis = 1, result_type = 'expand')
        else:
            data_df['recordedBy_name'] = data_df.apply(lambda row : get_personnel_details_from_email(row['recordedBy_email'], 'name', df_personnel), axis = 1, result_type = 'expand')

        if 'recordedBy_institution' in data_df.columns:
            data_df['recordedBy_institution'] = data_df.apply(lambda row : get_personnel_details_from_email(row['recordedBy_email'], 'institution', df_personnel, row['recordedBy_institution']), axis = 1, result_type = 'expand')
        else:
            data_df['recordedBy_institution'] = data_df.apply(lambda row : get_personnel_details_from_email(row['recordedBy_email'], 'institution', df_personnel), axis = 1, result_type = 'expand')

        if 'recordedBy_orcid' in data_df.columns:
            data_df['recordedBy_orcid'] = data_df.apply(lambda row : get_personnel_details_from_email(row['recordedBy_email'], 'orcid', df_personnel, row['recordedBy_orcid']), axis = 1, result_type = 'expand')
        else:
            data_df['recordedBy_orcid'] = data_df.apply(lambda row : get_personnel_details_from_email(row['recordedBy_email'], 'orcid', df_personnel), axis = 1, result_type = 'expand')

    if 'pi_email' in data_df.columns:
        if 'pi_name' in data_df.columns:
            data_df['pi_name'] = data_df.apply(lambda row : get_personnel_details_from_email(row['pi_email'], 'name', df_personnel, row['pi_name']), axis = 1, result_type = 'expand')
        else:
            data_df['pi_name'] = data_df.apply(lambda row : get_personnel_details_from_email(row['pi_email'], 'name', df_personnel), axis = 1, result_type = 'expand')

        if 'pi_institution' in data_df.columns:
            data_df['pi_institution'] = data_df.apply(lambda row : get_personnel_details_from_email(row['pi_email'], 'institution', df_personnel, row['pi_institution']), axis = 1, result_type = 'expand')
        else:
            data_df['pi_institution'] = data_df.apply(lambda row : get_personnel_details_from_email(row['pi_email'], 'institution', df_personnel), axis = 1, result_type = 'expand')

        if 'pi_orcid' in data_df.columns:
            data_df['pi_orcid'] = data_df.apply(lambda row : get_personnel_details_from_email(row['pi_email'], 'orcid', df_personnel, row['pi_orcid']), axis = 1, result_type = 'expand')
        else:
            data_df['pi_orcid'] = data_df.apply(lambda row : get_personnel_details_from_email(row['pi_email'], 'orcid', df_personnel), axis = 1, result_type = 'expand')

    return data_df

def get_personnel_details_from_email(email, setup, df_personnel, current_value='NULL'):
    '''
    email: string
    Email address to

    setup: string
    'institution', 'name' or 'orcid'. What you want to retrieve.

    df_personnel: Pandas dataframe
    The dataframe including details of all the personnel registered in the system
    Columns: id, first_name, last_name, institution, email, orcid, comment, created

    current_value: string. Default = 'NULL'
    Current value in dataframe.
    If the email is not registered in df_personnl, this won't work.
    In this case, the current_value is returned
    '''
    if email in df_personnel['email'].values:
        if setup in ['orcid', 'institution']:
            value = df_personnel.loc[df_personnel['email'] == email, setup].item()
        elif setup == 'name':
            first_name = df_personnel.loc[df_personnel['email'] == email, 'first_name'].item()
            last_name = df_personnel.loc[df_personnel['email'] == email, 'last_name'].item()
            value = first_name + ' ' + last_name
        return value
    else:
        return current_value

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

def prepare_and_check(df_subconfig, required, CRUISE_NUMBER, header_row, new, goods):

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
        new=new,
        firstrow = firstrow,
        old_ids = False
        )

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

    goods.append(good)

    return df_subconfig, goods

def df_to_dict_to_submit(df_to_submit, output_config_dict, extra_fields_dict, cf_standard_names, dwc_terms, CRUISE_NUMBER, filename):

    if 'parentid' in df_to_submit:
        df_to_submit = propegate_parents_to_children(df_to_submit,DB, CRUISE_NUMBER)
    df_to_submit.columns = df_to_submit.columns.str.lower()

    fields_to_submit_dict = {} # dictionary to populate with with fields, values and formatting requirements to submit to metadata catalogue table in database
    fields_to_submit_dict['columns'] = {}
    fields_to_submit_dict['hstore'] = {}
    metadata_columns_list = CONFIG["metadata_catalogue"]["fields_to_use_as_columns"]

    personnel_details_dict = get_dict_for_list_of_fields(['recordedBy_name', 'recordedBy_email', 'recordedBy_orcid', 'recordedBy_institution', 'pi_name', 'pi_email', 'pi_orcid', 'pi_institution'],FIELDS_FILEPATH)
    for field, vals in personnel_details_dict.items():
        fields_to_submit_dict['columns'][field] = vals
        if field.lower() in df_to_submit.columns:
            fields_to_submit_dict['columns'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
        else:
            fields_to_submit_dict['columns'][field]['value'] = ['NULL' for value in range(len(df_to_submit))]

    inherited_columns = df_to_submit.columns

    for requirement in output_config_dict['Data'].keys():
        if requirement not in ['Required CSV', 'Source']:
            for field, vals in output_config_dict['Data'][requirement].items():
                if field.lower() in df_to_submit.columns:
                    if field in metadata_columns_list:
                        fields_to_submit_dict['columns'][field] = output_config_dict['Data'][requirement][field]
                        fields_to_submit_dict['columns'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                    else:
                        fields_to_submit_dict['hstore'][field] = output_config_dict['Data'][requirement][field]
                        fields_to_submit_dict['hstore'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                    inherited_columns = [col for col in inherited_columns if col != field.lower()]

    for field, vals in extra_fields_dict.items():
        if field.lower() in df_to_submit.columns:
            if field in metadata_columns_list:
                fields_to_submit_dict['columns'][field] = vals
                fields_to_submit_dict['columns'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
            else:
                fields_to_submit_dict['hstore'][field] = vals
                fields_to_submit_dict['hstore'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
            inherited_columns = [col for col in inherited_columns if col != field.lower()]

    for dwc_term in dwc_terms:
        if dwc_term['id'].lower() in df_to_submit.columns and dwc_term['id'] not in fields_to_submit_dict['columns'].keys() and dwc_term['id'] not in fields_to_submit_dict['hstore'].keys():
            if dwc_term['id'] in metadata_columns_list:
                fields_to_submit_dict['columns'][dwc_term['id']] = dwc_term
                fields_to_submit_dict['columns'][dwc_term['id']]['value'] = [format_form_value(field, [value], dwc_term['format']) for value in list(df_to_submit[dwc_term['id'].lower()])]
            else:
                fields_to_submit_dict['hstore'][dwc_term['id']] = dwc_term
                fields_to_submit_dict['hstore'][dwc_term['id']]['value'] = [format_form_value(field, [value], dwc_term['format']) for value in list(df_to_submit[dwc_term['id'].lower()])]
            inherited_columns = [col for col in inherited_columns if col != dwc_term['id'].lower()]

    for cf_standard_name in cf_standard_names:
        if cf_standard_name['id'].lower() in df_to_submit.columns and cf_standard_name['id'] not in fields_to_submit_dict['columns'].keys() and cf_standard_name['id'] not in fields_to_submit_dict['hstore'].keys():
            if cf_standard_name['id'] in metadata_columns_list:
                fields_to_submit_dict['columns'][cf_standard_name['id']] = cf_standard_name
                fields_to_submit_dict['columns'][cf_standard_name['id']]['value'] = [format_form_value(field, [value], cf_standard_name['format']) for value in list(df_to_submit[cf_standard_name['id'].lower()])]
            else:
                fields_to_submit_dict['hstore'][cf_standard_name['id']] = cf_standard_name
                fields_to_submit_dict['hstore'][cf_standard_name['id']]['value'] = [format_form_value(field, [value], cf_standard_name['format']) for value in list(df_to_submit[cf_standard_name['id'].lower()])]
            inherited_columns = [col for col in inherited_columns if col != cf_standard_name['id'].lower()]

    inheritable = CONFIG["metadata_catalogue"]["fields_to_inherit"]
    weak = CONFIG["metadata_catalogue"]["fields_to_inherit_if_not_logged_for_children"]
    inherited_columns = [field for field in inherited_columns if field not in ['pi_name', 'pi_institution', 'pi_orcid', 'pi_email', 'recordedby_name', 'recordedby_email', 'recordedby_orcid', 'recordedby_institution']]
    inherited_columns = [field for field in inheritable+weak if field.lower() in inherited_columns]

    inherited_fields_dict = get_dict_for_list_of_fields(inherited_columns, FIELDS_FILEPATH)

    for field, vals in inherited_fields_dict.items():
        if field.lower() in df_to_submit.columns:
            if field in metadata_columns_list:
                fields_to_submit_dict['columns'][field] = vals
                fields_to_submit_dict['columns'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
            else:
                fields_to_submit_dict['hstore'][field] = vals
                fields_to_submit_dict['hstore'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]

    record_details = get_dict_for_list_of_fields(['created','modified','history','recordSource'],FIELDS_FILEPATH)
    fields_to_submit_dict['columns']['created'] = record_details['created']
    fields_to_submit_dict['columns']['modified'] = record_details['modified']
    fields_to_submit_dict['columns']['history'] = record_details['history']
    fields_to_submit_dict['columns']['recordSource'] = record_details['recordSource']

    fields_to_submit_dict['columns']['created']['value'] = [dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") for n in range(len(df_to_submit))]
    fields_to_submit_dict['columns']['modified']['value'] = [dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") for n in range(len(df_to_submit))]
    fields_to_submit_dict['columns']['history']['value'] = [dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record uploaded from spreadsheet, filename " + filename) for n in range(len(df_to_submit))]
    fields_to_submit_dict['columns']['recordSource']['value'] = ["Record uploaded from spreadsheet, filename " + filename for n in range(len(df_to_submit))]

    return fields_to_submit_dict

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

            if request.form['submitbutton'] == 'new':
                new = True
            elif request.form['submitbutton'] == 'update':
                new = False

            already_uploaded_files = get_all_sources(DB, CRUISE_NUMBER)

            if str(f.filename) in already_uploaded_files and new == True:
                errors.append(f'''A file called {f.filename} has already been uploaded.<br>
                Have these records already been registered?<br>
                If so, please select to update existing records instead<br>
                If these records have not been registered already, please rename your file.
                ''')
                good = False

            if warnings != []:
                for warning in warnings:
                    flash(warning, category='warning')
            if good == False:
                for error in errors:
                    flash(error, category='error')

            else:

                # Merging multiple pi details columns and recordedBy details columns
                pi_cols = []
                recordedBy_cols = []
                for col in data_df.columns:
                    if col.startswith('pi_details'):
                        pi_cols.append(col)
                    elif col.startswith('recordedBy') and col not in ['recordedBy_name','recordedBy_email','recordedBy_institution','recordedBy_orcid']:
                        recordedBy_cols.append(col)

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

                if 'recordedBy_email' in data_df.columns or 'pi_email' in data_df.columns:
                    data_df = reassign_personnel_based_on_email(data_df, df_personnel)

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
                    output_config_dicts = {}
                    extra_fields_dicts = {}
                    df_subconfigs_dict = {}
                    goods = []

                    for subconfig in subconfigs_included:

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

                        df_subconfig, goods = prepare_and_check(df_subconfig, required, CRUISE_NUMBER, header_row, new, goods)

                        output_config_dicts[subconfig] = output_config_dict
                        extra_fields_dicts[subconfig] = extra_fields_dicts
                        df_subconfigs_dict[subconfig] = df_subconfig

                    if False in goods:
                        if new == False:
                            flash('No records were updated', category='error')
                        else:
                            flash('No records were uploaded', category='error')
                    else:

                        for subconfig in subconfigs_included:
                            if subconfig == 'Niskin bottles':
                                df_subconfigs_dict[subconfig]['eventID'] = df_subconfigs_dict[subconfig]['id']

                            # 4. Only upload records once checker passed for all dfs (the whole sheet)
                            fields_to_submit_dict = df_to_dict_to_submit(df_subconfigs_dict[subconfig], output_config_dicts[subconfig], extra_fields_dicts[subconfig], cf_standard_names, dwc_terms, CRUISE_NUMBER, f.filename)

                            if new == True:
                                insert_into_metadata_catalogue(fields_to_submit_dict, len(df_subconfigs_dict[subconfig]), DB, CRUISE_NUMBER)
                            elif new == False:
                                IDs = df_subconfigs_dict[subconfig]['id'].values.tolist()
                                update_record_metadata_catalogue(fields_to_submit_dict, DB, CRUISE_NUMBER, IDs)

                        flash('Data from file uploaded successfully!', category='success')

                        # Isolate IDs for only highest level (parents) in sheet
                        IDs = list(data_df['id'])
                        df = get_metadata_for_list_of_ids(DB, CRUISE_NUMBER, IDs)
                        filtered_df = df[~df['parentid'].isin(df['id'])]
                        IDs = filtered_df['id'].tolist()
                        ii = propegate_update_to_children(IDs, DB, CRUISE_NUMBER)

                        if ii > 0:
                            flash('Relevant metadata copied to children', category='success')

                        return redirect('/')

                else:
                    subconfig = 'Activities'
                    data_df['subconfig'] = subconfig
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
                    goods = []

                    # If column not present, adding it as blank.
                    # Activities require 2 of the 4 fields to be included. Flagging error if not. Checker doesn't work without this addition
                    for col in ['minimumDepthInMeters', 'maximumDepthInMeters', 'minimumElevationInMeters', 'maximumElevationInMeters']:
                        if col not in df_subconfig.columns:
                            df_subconfig[col] = np.nan

                    df_subconfig, goods = prepare_and_check(df_subconfig, required, CRUISE_NUMBER, header_row, new, goods)

                    if False in goods:
                        if new == False:
                            flash('No records were uploaded', category='error')
                        else:
                            flash('No records were updated', category='error')
                    else:

                        df_subconfig['eventID'] = df_subconfig['id']

                        try:
                            fields_to_submit_dict = df_to_dict_to_submit(df_subconfig, output_config_dict, extra_fields_dict, cf_standard_names, dwc_terms, CRUISE_NUMBER, f.filename)

                            if new == True:
                                insert_into_metadata_catalogue(fields_to_submit_dict, len(df_subconfig), DB, CRUISE_NUMBER)
                                flash('Data from file uploaded successfully!', category='success')
                            elif new == False:
                                IDs = df_subconfig['id'].values.tolist()
                                update_record_metadata_catalogue(fields_to_submit_dict, DB, CRUISE_NUMBER, IDs)
                                flash('Records successfully updated using data from file!', category='success')

                                ii = propegate_update_to_children(IDs, DB, CRUISE_NUMBER)
                                if ii > 0:
                                    flash('Relevant metadata copied to children', category='success')

                            return redirect('/')
                        except:
                            flash('Unexpected fail upon upload. Please check your file and try again, or contact someone for help', category='error')

    return render_template(
    "submitSpreadsheet.html"
    )
