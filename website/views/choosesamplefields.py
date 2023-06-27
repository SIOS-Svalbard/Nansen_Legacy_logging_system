from flask import Blueprint, render_template, request, flash, redirect, send_file
import psycopg2
import psycopg2.extras
from website.lib.get_data import get_cruise, get_user_setup, get_gears_list, get_subconfig_for_sampletype, df_from_database
from website import DB, METADATA_CATALOGUE, FIELDS_FILEPATH, CRUISE_NUMBER
import numpy as np
import pandas as pd
import os
import yaml
from website.Learnings_from_AeN_template_generator.website.lib.create_template import create_template
from website.lib.get_setup_for_configuration import get_setup_for_configuration
from website.lib.other_functions import combine_fields_dictionaries

choosesamplefields = Blueprint('choosesamplefields', __name__)

@choosesamplefields.route('/logSamples/parentid=<parentID>/chooseSampleFields/sampletype=<sampleType>', methods=['GET', 'POST'])
def choose_sample_fields(parentID,sampleType):
    '''
    Generate template html page code
    '''
    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

    config = 'Learnings from Nansen Legacy logging system'
    subconfig = get_subconfig_for_sampletype(sampleType, DB)

    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

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

    most_likely_same_for_all_samples = [
    'parentID',
    'pi_details',
    'recordedBy',
    'sampleType',
    'gearType',
    'samplingProtocolDoc',
    'samplingProtocolSection',
    'samplingProtocolVersion'
    ]

    for key, val in output_config_dict['Data']['Required'].items():
        if key in most_likely_same_for_all_samples:
            val['checked'] = ['same']
        else:
            val['checked'] = ['vary']

    for key, val in output_config_dict['Data']['Recommended'].items():
        if key in most_likely_same_for_all_samples:
            val['checked'] = ['same']
        else:
            val['checked'] = ['vary']

    num_samples = 1
    current_setup = ''

    if request.method == 'POST':

        form_input = request.form.to_dict(flat=False)
        all_form_keys = request.form.keys()

        # 1. Preserve the values added in the form for each field by adding them to the relevant dictionaries
        for sheet in output_config_dict.keys():
            for requirement in output_config_dict[sheet].keys():
                if requirement not in ['Required CSV', 'Source']:
                    for field, vals in output_config_dict[sheet][requirement].items():
                        if field in form_input:
                            vals['checked'] = form_input[field]
                        else:
                            vals['checked'] = ['']

        # 2. Adding extra fields selected by user

        # CF standard names
        for field in cf_standard_names:
            for sheet in added_cf_names_dic.keys():
                if sheet not in ['Required CSV', 'Source']:
                    for form_key in all_form_keys:
                        if form_key == field['id']:
                            added_cf_names_dic[sheet][field['id']] = {}
                            added_cf_names_dic[sheet][field['id']]['id'] = field['id']
                            added_cf_names_dic[sheet][field['id']]['disp_name'] = field['id']
                            added_cf_names_dic[sheet][field['id']]['valid'] = field['valid']
                            if field["description"] == None:
                                field["description"] = ""
                            added_cf_names_dic[sheet][field['id']]['description'] = f"{field['description']} \ncanonical units: {field['canonical_units']}"
                            added_cf_names_dic[sheet][field['id']]['format'] = field['format']
                            added_cf_names_dic[sheet][field['id']]['grouping'] = field['grouping']
                            if field['id'] in form_input:
                                added_cf_names_dic[sheet][field['id']]['checked'] = form_input[field['id']]
                            else:
                                added_cf_names_dic[sheet][field['id']]['checked'] = ['']

        # Darwin Core terms
        for sheet in dwc_terms_not_in_config.keys():
            for term in dwc_terms_not_in_config[sheet]:
                for form_key in all_form_keys:
                    if form_key == term['id']:
                        added_dwc_terms_dic[sheet][term['id']] = {}
                        added_dwc_terms_dic[sheet][term['id']]['id'] = term['id']
                        added_dwc_terms_dic[sheet][term['id']]['disp_name'] = term['id']
                        added_dwc_terms_dic[sheet][term['id']]['valid'] = term['valid']
                        if term["description"] == None:
                            term["description"] = ""
                        added_dwc_terms_dic[sheet][term['id']]['description'] = term['description']
                        added_dwc_terms_dic[sheet][term['id']]['format'] = term["format"]
                        added_dwc_terms_dic[sheet][term['id']]['grouping'] = term["grouping"]
                        if term['id'] in form_input:
                            added_dwc_terms_dic[sheet][term['id']]['checked'] = form_input[term['id']]
                        else:
                            added_dwc_terms_dic[sheet][term['id']]['checked'] = ['']

        # Other fields (not CF standard names or DwC terms - terms designed for the template generator and logging system)
        for field, vals in extra_fields_dict.items():
            for form_key in all_form_keys:
                if field == form_key:
                    added_fields_dic['Data'][field] = vals
                    if field in form_input:
                        added_fields_dic[sheet][field]['checked'] = form_input[field]
                    else:
                        added_fields_dic[sheet][field]['checked'] = ['']

        num_samples = int(form_input['num_samples'][0])

        if form_input['submitbutton'] == ['addfields']:
            pass

        elif form_input['submitbutton'] == ['generateTemplate']:

            data_df = pd.DataFrame(index=np.arange(num_samples))
            for field, val in form_input.items():
                if field not in ['submitbutton','setupName','num_samples','userSetup']:
                    data_df[field] = ''
            data_df['parentID'] = parentID
            data_df['sampleType'] = sampleType

            gear_list = get_gears_list(DB)
            if sampleType in gear_list:
                data_df['gearType'] = sampleType
            else:
                data_df['gearType'] = None

            fields_list = data_df.columns

            filepath = f'/tmp/{CRUISE_NUMBER}_{sampleType}_parent{parentID}.xlsx'

            template_fields_dict = combine_fields_dictionaries(
                output_config_dict,
                added_fields_dic,
                added_cf_names_dic,
                added_dwc_terms_dic,
                data_df
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

        elif form_input['submitbutton'] == ['loadSetup']:

            current_setup = form_input['userSetup'][0]
            userSetup = get_user_setup(DB, CRUISE_NUMBER, current_setup) # json of setup

            # adding data for fields in setup to dictionaries to be displayed through HTML
            for key, val in userSetup.items():
                if '|' in val:
                    checked = val.split(' | ')
                else:
                    checked = val

                if key in output_config_dict['Data']['Required'].keys():
                    output_config_dict['Data']['Required'][key]['checked'] = checked
                if key in output_config_dict['Data']['Recommended'].keys():
                    output_config_dict['Data']['Recommended'][key]['checked'] = checked

                for field in cf_standard_names:
                    if field['id'] == key:
                        added_cf_names_dic['Data'][field['id']] = field
                        added_cf_names_dic['Data'][field['id']]['checked'] = checked

                for field in dwc_terms_not_in_config['Data']:
                    if field['id'] == key:
                        added_dwc_terms_dic['Data'][field['id']] = field
                        added_dwc_terms_dic['Data'][field['id']]['checked'] = checked

                for field, vals in extra_fields_dict.items():
                    if field == key:
                        added_fields_dic['Data'][field] = vals
                        added_fields_dic['Data'][field]['checked'] = checked

            # Fields not included in setup shouldn't be checked.
            for key, val in output_config_dict['Data']['Recommended'].items():
                if key not in userSetup.keys():
                    val['checked'] = ['']

        else:

            good = True
            errors = []

            if form_input['setupName'] == ['']:
                if form_input['submitbutton'] == ['saveSetup']:
                    setupName = 'temporary'
                    good = False
                    errors.append('Please enter a name for this setup.')
                else:
                    setupName = 'temporary'
            else:
                setupName = form_input['setupName'][0]

            query = f'SELECT setupName FROM user_field_setups_{CRUISE_NUMBER};'
            df = df_from_database(query,DB)
            existing_user_setups = df['setupname'].tolist()

            if setupName in existing_user_setups and setupName != 'temporary':
                good = False
                errors.append(f'Setup with name {setupName} already exists. Please choose another name.')

            for key, val in form_input.items():
                if len(val) > 1:
                    good = False
                    errors.append(f'Can only tick one box per field: {key}')

            setup = {}

            for sheet in output_config_dict.keys():
                for requirement in output_config_dict[sheet].keys():
                    if requirement not in ['Required CSV', 'Source']:
                        for field, vals in output_config_dict[sheet][requirement].items():
                            if vals['checked'] == [''] and requirement == 'Required':
                                good = False
                                errors.append(f"At least one box must be ticked for all required fields: {vals['disp_name']}")
                            else:
                                setup[field] = vals['checked']

            for sheet in added_cf_names_dic.keys():
                for field, vals in added_cf_names_dic[sheet].items():
                    setup[field] = vals['checked']

            for sheet in added_dwc_terms_dic.keys():
                for field, vals in added_dwc_terms_dic[sheet].items():
                    setup[field] = vals['checked']

            for sheet in added_fields_dic.keys():
                for field, vals in added_fields_dic[sheet].items():
                    setup[field] = vals['checked']

            setup = str(setup).replace('\'','"')

            if good == False:
                for error in errors:
                    flash(error, category='error')

            else:

                conn = psycopg2.connect(**DB)
                cur = conn.cursor()

                if setupName == 'temporary':
                    exe_str = f"UPDATE user_field_setups_{CRUISE_NUMBER} SET setup = '{setup}', created = CURRENT_TIMESTAMP WHERE setupName = '{setupName}';"
                else:
                    exe_str = f"INSERT INTO user_field_setups_{CRUISE_NUMBER} (setupName, setup, created) VALUES ('{setupName}', '{setup}', CURRENT_TIMESTAMP);"

                cur.execute(exe_str)
                conn.commit()
                cur.close()
                conn.close()

                if setupName != 'temporary':
                    current_setup = setupName

                if form_input['submitbutton'] == ['saveSetup']:
                    flash('Setup saved!', category='success')

                elif form_input['submitbutton'] == ['logForm']:

                    if current_setup == '':
                        current_setup = 'temporary'
                    return redirect(f'/logSamples/parentid={parentID}/form/sampletype={sampleType}&num={num_samples}&setup={current_setup}')

    query = f"SELECT setupName FROM user_field_setups_{CRUISE_NUMBER} WHERE setupName != 'temporary';"
    df = df_from_database(query,DB)
    existing_user_setups = sorted(df['setupname'].tolist())

    return render_template(
    "chooseSampleFields.html",
    parentID=parentID,
    sampleType=sampleType,
    output_config_dict=output_config_dict,
    extra_fields_dict = extra_fields_dict,
    groups = groups,
    num_samples = num_samples,
    existing_user_setups = existing_user_setups,
    current_setup = current_setup,
    cf_standard_names=cf_standard_names,
    dwc_terms_not_in_config=dwc_terms_not_in_config,
    added_fields_dic=added_fields_dic,
    added_cf_names_dic=added_cf_names_dic,
    added_dwc_terms_dic=added_dwc_terms_dic
    )
