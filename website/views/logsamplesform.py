from flask import Blueprint, render_template, request, flash, redirect, send_file, session
import psycopg2
import psycopg2.extras
import uuid
from website.lib.get_data import get_cruise, get_user_setup, get_metadata_for_record_and_ancestors, get_metadata_for_id, get_personnel_df, get_gears_list, get_subconfig_for_sampletype
from website.lib.propegate_parents_to_children import propegate_parents_to_children
from website.lib.input_update_records import insert_into_metadata_catalogue
from website.lib.checker import run as checker
from website.lib.other_functions import split_personnel_list, get_title, format_form_value, format_columns
from website import DB, FIELDS_FILEPATH, CONFIG
import numpy as np
from datetime import datetime as dt
import pandas as pd
import os
import yaml
from website.lib.get_setup_for_configuration import get_setup_for_configuration
from website.Learnings_from_AeN_template_generator.website.lib.get_configurations import get_list_of_subconfigs
from website.lib.get_dict_for_list_of_fields import get_dict_for_list_of_fields
from website.lib.other_functions import combine_fields_dictionaries
from website.Learnings_from_AeN_template_generator.website.lib.create_template import create_template

logsamplesform = Blueprint('logsamplesform', __name__)

@logsamplesform.route('/logSamples/parentid=<parentID>/form/sampletype=<sampleType>&num=<num_samples>&setup=<current_setup>', methods=['GET', 'POST'])
def log_samples_form(parentID,sampleType,num_samples,current_setup):
    '''
    Generate template html page code
    '''

    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

    config = 'Learnings from Nansen Legacy logging system'
    list_of_subconfigs = get_list_of_subconfigs(config='Learnings from Nansen Legacy logging system')
    subconfig = get_subconfig_for_sampletype(sampleType, DB)

    gear_list = get_gears_list(DB)
    if sampleType in gear_list:
        gearType = sampleType
    else:
        gearType = None

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
        required = required + ['pi_name', 'pi_email', 'pi_orcid', 'pi_institution']
    if 'recordedBy' in required:
        required.remove('recordedBy')
        required = required + ['recordedBy_name', 'recordedBy_email', 'recordedBy_orcid', 'recordedBy_institution']

    userSetup = get_user_setup(DB, CRUISE_NUMBER, current_setup) # json of setup

    # adding data for fields in setup to dictionaries to be displayed through HTML
    for key, val in userSetup.items():
        if '|' in val:
            checked = val.split(' | ')
        else:
            checked = val

        for sheet in output_config_dict.keys():
            for requirement in output_config_dict[sheet].keys():
                if requirement not in ['Required CSV', 'Source']:
                    for field, vals in output_config_dict[sheet][requirement].items():
                        if field == key:
                            if checked == ['same']:
                                if key == 'sampleType':
                                    vals['value'] = sampleType
                                elif key == 'gearType':
                                    vals['value'] = gearType
                                else:
                                    vals['value'] = ''
                            elif checked == ['vary']:
                                if key == 'sampleType':
                                    vals['value'] = [sampleType] * int(num_samples)
                                elif key == 'gearType':
                                    vals['value'] = [gearType] * int(num_samples)
                                else:
                                    vals['value'] = [''] * int(num_samples)
                            else:
                                vals['value'] = ''
                            vals['checked'] = checked


        # CF standard names
        for field in cf_standard_names:
            for sheet in added_cf_names_dic.keys():
                if sheet not in ['Required CSV', 'Source']:
                    if key == field['id']:
                        added_cf_names_dic[sheet][field['id']] = {}
                        added_cf_names_dic[sheet][field['id']]['id'] = field['id']
                        added_cf_names_dic[sheet][field['id']]['disp_name'] = field['id']
                        added_cf_names_dic[sheet][field['id']]['valid'] = field['valid']
                        if field["description"] == None:
                            field["description"] = ""
                        added_cf_names_dic[sheet][field['id']]['description'] = f"{field['description']} \ncanonical units: {field['canonical_units']}"
                        added_cf_names_dic[sheet][field['id']]['format'] = field['format']
                        added_cf_names_dic[sheet][field['id']]['grouping'] = field['grouping']
                        if field['id'] in userSetup.keys():
                            added_cf_names_dic[sheet][field['id']]['checked'] = checked
                        else:
                            added_cf_names_dic[sheet][field['id']]['checked'] = ['']
                        if checked == ['same']:
                            added_cf_names_dic[sheet][field['id']]['value'] = ''
                        elif checked == ['vary']:
                            added_cf_names_dic[sheet][field['id']]['value'] = [''] * int(num_samples)
                        else:
                            added_cf_names_dic[sheet][field['id']]['value'] = ''

        # Darwin Core terms
        for sheet in dwc_terms_not_in_config.keys():
            for term in dwc_terms_not_in_config[sheet]:
                if key == term['id']:
                    added_dwc_terms_dic[sheet][term['id']] = {}
                    added_dwc_terms_dic[sheet][term['id']]['id'] = term['id']
                    added_dwc_terms_dic[sheet][term['id']]['disp_name'] = term['id']
                    added_dwc_terms_dic[sheet][term['id']]['valid'] = term['valid']
                    if term["description"] == None:
                        term["description"] = ""
                    added_dwc_terms_dic[sheet][term['id']]['description'] = term['description']
                    added_dwc_terms_dic[sheet][term['id']]['format'] = term["format"]
                    added_dwc_terms_dic[sheet][term['id']]['grouping'] = term["grouping"]
                    if term['id'] in userSetup.keys():
                        added_dwc_terms_dic[sheet][term['id']]['checked'] = checked
                    else:
                        added_dwc_terms_dic[sheet][term['id']]['checked'] = ['']
                    if checked == ['same']:
                        added_dwc_terms_dic[sheet][term['id']]['value'] = ''
                    elif checked == ['vary']:
                        added_dwc_terms_dic[sheet][term['id']]['value'] = [''] * int(num_samples)
                    else:
                        added_dwc_terms_dic[sheet][term['id']]['value'] = ''

        # Other fields (not CF standard names or DwC terms - terms designed for the template generator and logging system)
        for field, vals in extra_fields_dict.items():
            if field == key:
                added_fields_dic['Data'][field] = vals
                added_fields_dic['Data'][field]['checked'] = checked
                if checked == 'same':
                    if key == 'sampleType':
                        added_fields_dic['Data'][field]['value'] = sampleType
                    elif key == 'gearType':
                        added_fields_dic['Data'][field]['value'] = gearType
                    else:
                        added_fields_dic['Data'][field]['value'] = ''
                elif checked == 'vary':
                    if key == 'sampleType':
                        added_fields_dic['Data'][field]['value'] = [sampleType] * int(num_samples)
                    elif key == 'gearType':
                        added_fields_dic['Data'][field]['value'] = [gearType] * int(num_samples)
                    else:
                        added_fields_dic['Data'][field]['value'] = [''] * int(num_samples)
                if checked == ['same']:
                    added_fields_dic['Data'][field]['value'] = ''
                elif checked == ['vary']:
                    added_fields_dic['Data'][field]['value'] = [''] * int(num_samples)
                else:
                    added_fields_dic['Data'][field]['value'] = ''

    parent_df = get_metadata_for_id(DB, CRUISE_NUMBER, parentID)
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
    parent_details = get_dict_for_list_of_fields(parent_fields,FIELDS_FILEPATH)

    for parent_field in parent_fields:
        parent_details[parent_field]['value'] = parent_df[parent_field.lower()][0]

    if request.method == 'POST':

        form_input = request.form.to_dict(flat=False)

        df_personnel = get_personnel_df(DB=DB, CRUISE_NUMBER=CRUISE_NUMBER, table='personnel')

        cols = userSetup.keys()

        # Initialising dataframe
        df = pd.DataFrame(columns = cols, index=np.arange(int(num_samples)))
        df_to_submit = format_columns(df, output_config_dict, added_fields_dic, added_cf_names_dic, added_dwc_terms_dic)

        df_to_submit['parentID'] = parentID
        fields_to_submit_list = []
        rows = list(range(int(num_samples)))

        # 1. Preserve the values added in the form for each field by adding them to the relevant dictionaries
        # a: First for values constant for all samples
        # config fields
        for sheet in output_config_dict.keys():
            for requirement in output_config_dict[sheet].keys():
                if requirement not in ['Required CSV', 'Source']:
                    for field, vals in output_config_dict[sheet][requirement].items():
                        fields_to_submit_list.append(field)
                        if field in form_input:
                            vals['value'] = value = format_form_value(field, form_input[field], vals['format'])
                            if type(value) == list:
                                if len(value) == 1:
                                    df_to_submit[field] = value * len(df_to_submit)
                                else:
                                    df_to_submit[field] = ' | '.join(value)
                            else:
                                df_to_submit[field] = value
                        else:
                            if field in ['pi_details', 'recordedBy']:
                                vals['value'] = []

        # cf_standard_names
        for field, vals in added_cf_names_dic['Data'].items():
            if field in form_input:
                fields_to_submit_list.append(field)
                vals['value'] = value = format_form_value(field, form_input[field], vals['format'])
                if type(value) == list:
                    df_to_submit[field] = value * len(df_to_submit)
                else:
                    df_to_submit[field] = value

        # darwin core terms
        for field, vals in added_dwc_terms_dic['Data'].items():
            if field in form_input:
                fields_to_submit_list.append(field)
                vals['value'] = value = format_form_value(field, form_input[field], vals['format'])
                if type(value) == list:
                    df_to_submit[field] = value * len(df_to_submit)
                else:
                    df_to_submit[field] = value

        # other fields
        for field, vals in added_fields_dic['Data'].items():
            if field in form_input:
                fields_to_submit_list.append(field)
                vals['value'] = value = format_form_value(field, form_input[field], vals['format'])
                if type(value) == list:
                    if len(value) == 1:
                        df_to_submit[field] = value * len(df_to_submit)
                    else:
                        df_to_submit[field] = ' | '.join(value)
                else:
                    df_to_submit[field] = value

        # b: Second for values different for all samples
        fields_varied = []
        num_cols_form_table = 0 # Number of columns in table
        num_cells_empty_for_row = {}
        for key, value in form_input.items():
            if '|' in key:
                field, row = key.split('|')
                fields_varied.append(field)
                fields_to_submit_list.append(field)
                row = int(row)
                if row == rows[0]:
                    num_cols_form_table += 1
                if row not in num_cells_empty_for_row.keys():
                    num_cells_empty_for_row[row] = 0

                if row in rows:
                    if len(value) == 1 and field not in ['pi_details', 'recordedBy']:

                        for requirement in output_config_dict['Data'].keys():
                            if requirement not in ['Required CSV', 'Source']:
                                for term, vals in output_config_dict['Data'][requirement].items():
                                    if term == field:
                                        formatted_value = format_form_value(field, value, vals['format'])
                                        df_to_submit.loc[row, field] = formatted_value

                        for term, vals in added_cf_names_dic['Data'].items():
                            if term == field:
                                formatted_value = format_form_value(field, value, vals['format'])
                                df_to_submit.loc[row, field] = formatted_value

                        for term, vals in added_dwc_terms_dic['Data'].items():
                            if term == field:
                                formatted_value = format_form_value(field, value, vals['format'])
                                df_to_submit.loc[row, field] = formatted_value

                        for term, vals in added_fields_dic['Data'].items():
                            if term == field:
                                formatted_value = format_form_value(field, value, vals['format'])
                                df_to_submit.loc[row, field] = formatted_value

                    elif field in ['pi_details', 'recordedBy']:
                        df_to_submit.loc[row, field] = ' | '.join(format_form_value(field, value, 'text'))

                    if formatted_value in ['', 'NULL', np.nan, None]:
                        num_cells_empty_for_row[row] += 1

        if 'submit' in form_input.keys():
            if form_input['submit'] == ['generateExcel']:
                num_rows_to_submit = num_samples
        else:
            if num_cols_form_table > 0:
                # Step 1: Create a list of indices that satisfy the condition
                indices_to_remove = [idx for idx, _ in df_to_submit.iterrows() if num_cells_empty_for_row[idx] == num_cols_form_table]
                # Step 2: Drop the rows using the indices list
                df_to_submit = df_to_submit.drop(indices_to_remove)
                num_rows_to_submit = len(df_to_submit)
            else:
                num_rows_to_submit = num_samples

        # Populate dictionaries from df for fields whose values vary for each row
        fields_varied = list(set(fields_varied))

        for field in fields_varied:
            for requirement in output_config_dict['Data'].keys():
                if requirement not in ['Required CSV', 'Source']:
                    for term, vals in output_config_dict['Data'][requirement].items():
                        if field == term:
                            vals['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field])]
                            if field == 'id':
                                vals['value'] = ['' if id == 'NULL' else id for id in list(df_to_submit[field])]
            for term, vals in added_cf_names_dic['Data'].items():
                if term == field:
                    vals['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field])]

            for term, vals in added_dwc_terms_dic['Data'].items():
                if term == field:
                    vals['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field])]

            for term, vals in added_fields_dic['Data'].items():
                if term == field:
                    vals['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field])]

        if 'movefieldtovary' in form_input.keys():
            fieldtovary = form_input['movefieldtovary'][0]
            userSetup[fieldtovary] = ['vary']

            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            userSetup = str(userSetup).replace('\'','"')

            exe_str = f"UPDATE user_field_setups_{CRUISE_NUMBER} SET setup = '{str(userSetup)}', created = CURRENT_TIMESTAMP WHERE setupName = 'temporary';"

            cur.execute(exe_str)
            conn.commit()
            cur.close()
            conn.close()

            return redirect(f'/logSamples/parentid={parentID}/form/sampletype={sampleType}&num={num_samples}&setup=temporary')

        elif 'movefieldtosame' in form_input.keys():
            fieldtovary = form_input['movefieldtosame'][0]
            userSetup[fieldtovary] = ['same']

            conn = psycopg2.connect(**DB)
            cur = conn.cursor()

            userSetup = str(userSetup).replace('\'','"')

            exe_str = f"UPDATE user_field_setups_{CRUISE_NUMBER} SET setup = '{str(userSetup)}', created = CURRENT_TIMESTAMP WHERE setupName = 'temporary';"

            cur.execute(exe_str)
            conn.commit()
            cur.close()
            conn.close()

            return redirect(f'/logSamples/parentid={parentID}/form/sampletype={sampleType}&num={num_samples}&setup=temporary')

        elif 'submit' in form_input.keys():

            if form_input['submit'] in [['submitForm'],['printLabels']]:

                if num_rows_to_submit == 0:
                    flash('Please enter metadata for at least one sample', category='error')
                    return redirect(f'/logSamples/parentid={parentID}/form/sampletype={sampleType}&num={num_samples}&setup=temporary')

                if 'pi_details' in fields_to_submit_list:
                    df_to_submit[['pi_name','pi_email','pi_orcid','pi_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['pi_details'], df_personnel), axis = 1, result_type = 'expand')
                    while 'pi_details' in fields_to_submit_list:
                        fields_to_submit_list.remove('pi_details')
                    fields_to_submit_list = fields_to_submit_list + ['pi_name', 'pi_email', 'pi_orcid', 'pi_institution']
                if 'recordedBy' in fields_to_submit_list:
                    df_to_submit[['recordedBy_name','recordedBy_email','recordedBy_orcid','recordedBy_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['recordedBy'], df_personnel), axis = 1, result_type = 'expand')
                    while 'recordedBy' in fields_to_submit_list:
                        fields_to_submit_list.remove('recordedBy')
                    fields_to_submit_list = fields_to_submit_list + ['recordedBy_name', 'recordedBy_email', 'recordedBy_orcid', 'recordedBy_institution']

                fields_to_submit_list = fields_to_submit_list + ['parentID']

                if 'pi_details' in required:
                    df_to_submit[['pi_name','pi_email','pi_orcid','pi_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['pi_details'], df_personnel), axis = 1, result_type = 'expand')
                    while 'pi_details' in required:
                        required.remove('pi_details')
                    required = required + ['pi_name', 'pi_email', 'pi_orcid', 'pi_institution']
                if 'recordedBy' in required:
                    df_to_submit[['recordedBy_name','recordedBy_email','recordedBy_orcid','recordedBy_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['recordedBy'], df_personnel), axis = 1, result_type = 'expand')
                    while 'recordedBy' in required:
                        required.remove('recordedBy')
                    required = required + ['recordedBy_name', 'recordedBy_email', 'recordedBy_orcid', 'recordedBy_institution']

                required = required + ['parentID']

                for col in df_to_submit.columns:
                    if col not in fields_to_submit_list and col != 'id':
                        df_to_submit.drop(col, axis=1, inplace=True)

                if 'id' not in df_to_submit.columns:
                    df_to_submit['id'] = [str(uuid.uuid4()) for ii in range(len(df_to_submit))]
                else:
                    df_to_submit['id'] = df_to_submit['id'].apply(lambda x: str(uuid.uuid4()) if x in ['NULL',np.nan] else x)

                good, errors = checker(
                    data=df_to_submit,
                    required=required,
                    DB=DB,
                    CRUISE_NUMBER=CRUISE_NUMBER,
                    new=True,
                    firstrow=1
                    )

                if good == False:
                    for error in errors:
                        flash(error, category='error')

                else:

                    df_to_submit = propegate_parents_to_children(df_to_submit,DB, CRUISE_NUMBER)
                    df_to_submit.columns = df_to_submit.columns.str.lower()

                    fields_to_submit_dict = {} # dictionary to populate with with fields, values and formatting requirements to submit to metadata catalogue table in database
                    fields_to_submit_dict['columns'] = {}
                    fields_to_submit_dict['hstore'] = {}
                    metadata_columns_list = CONFIG["metadata_catalogue"]["fields_to_use_as_columns"]

                    personnel_details_dict = get_dict_for_list_of_fields(['recordedBy_name', 'recordedBy_email', 'recordedBy_orcid', 'recordedBy_institution', 'pi_name', 'pi_email', 'pi_orcid', 'pi_institution'],FIELDS_FILEPATH)
                    for field, vals in personnel_details_dict.items():
                        fields_to_submit_dict['columns'][field] = vals
                        fields_to_submit_dict['columns'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]

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

                    for field, vals in added_fields_dic['Data'].items():
                        if field.lower() in df_to_submit.columns:
                            if field in metadata_columns_list:
                                fields_to_submit_dict['columns'][field] = vals
                                fields_to_submit_dict['columns'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                            else:
                                fields_to_submit_dict['hstore'][field] = vals
                                fields_to_submit_dict['hstore'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                            inherited_columns = [col for col in inherited_columns if col != field.lower()]

                    for field, vals in added_dwc_terms_dic['Data'].items():
                        if field.lower() in df_to_submit.columns:
                            if field in metadata_columns_list:
                                fields_to_submit_dict['columns'][field] = vals
                                fields_to_submit_dict['columns'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                            else:
                                fields_to_submit_dict['hstore'][field] = vals
                                fields_to_submit_dict['hstore'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                            inherited_columns = [col for col in inherited_columns if col != field.lower()]

                    for field, vals in added_cf_names_dic['Data'].items():
                        if field.lower() in df_to_submit.columns:
                            if field in metadata_columns_list:
                                fields_to_submit_dict['columns'][field] = vals
                                fields_to_submit_dict['columns'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                            else:
                                fields_to_submit_dict['hstore'][field] = vals
                                fields_to_submit_dict['hstore'][field]['value'] = [format_form_value(field, [value], vals['format']) for value in list(df_to_submit[field.lower()])]
                            inherited_columns = [col for col in inherited_columns if col != field.lower()]

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

                    fields_to_submit_dict['columns']['created']['value'] = [dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") for n in range(int(num_rows_to_submit))]
                    fields_to_submit_dict['columns']['modified']['value'] = [dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") for n in range(int(num_rows_to_submit))]
                    fields_to_submit_dict['columns']['history']['value'] = [dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record uploaded from GUI form for logging samples") for n in range(int(num_rows_to_submit))]
                    fields_to_submit_dict['columns']['recordSource']['value'] = ["Record uploaded from GUI form for logging samples" for n in range(int(num_rows_to_submit))]

                    insert_into_metadata_catalogue(fields_to_submit_dict, int(num_rows_to_submit), DB, CRUISE_NUMBER)

                    flash('Samples logged successfully!', category='success')

                    if form_input['submit'] == ['submitForm']:
                        return redirect(f'/logSamples/parentid={parentID}')

                    elif form_input['submit'] == ['printLabels']:

                        session['ids_to_print'] = fields_to_submit_dict['columns']['id']['value']
                        return redirect(f'/printLabelsForIDs')

            elif form_input['submit'] == ['generateExcel']:
                
                print(df_to_submit)

                filepath = f'/tmp/{CRUISE_NUMBER}_{sampleType}_parent{parentID}.xlsx'

                for field, vals in output_config_dict['Data']['Required'].items():
                    if vals['value'] in [[],['NULL'],'NULL']:
                        vals['value'] = ['']
                        df_to_submit[field] = ''
                for field, vals in output_config_dict['Data']['Recommended'].items():
                    if vals['value'] in [[],['NULL'],'NULL']:
                        vals['value'] = ['']
                        df_to_submit[field] = ''

                template_fields_dict = combine_fields_dictionaries(
                    output_config_dict,
                    added_fields_dic,
                    added_cf_names_dic,
                    added_dwc_terms_dic,
                    df_to_submit
                )

                create_template(
                    filepath = filepath,
                    template_fields_dict = template_fields_dict,
                    fields_filepath = FIELDS_FILEPATH,
                    config = config,
                    subconfig=subconfig,
                    metadata=False,
                    conversions=True,
                    split_personnel_columns=True
                )

                return send_file(filepath, as_attachment=True)

    trace = get_metadata_for_record_and_ancestors(DB, CRUISE_NUMBER, parentID)

    return render_template(
    "logSamplesForm.html",
    parentID=parentID,
    parent_details=parent_details,
    sampleType=sampleType,
    gearType=gearType,
    output_config_dict=output_config_dict,
    extra_fields_dict=extra_fields_dict,
    groups=groups,
    added_fields_dic=added_fields_dic,
    cf_standard_names=cf_standard_names,
    added_cf_names_dic=added_cf_names_dic,
    dwc_terms_not_in_config=dwc_terms_not_in_config,
    added_dwc_terms_dic=added_dwc_terms_dic,
    num_rows = int(num_samples),
    trace=trace,
    get_title=get_title
    )
