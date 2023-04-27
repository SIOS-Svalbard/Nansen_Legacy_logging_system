from flask import Blueprint, render_template, request, flash, redirect, send_file
import psycopg2
import psycopg2.extras
from website.lib.get_data import get_cruise, get_user_setup
from . import DB, METADATA_CATALOGUE
import numpy as np
import pandas as pd
import os
import yaml

choosesamplefields = Blueprint('choosesamplefields', __name__)

@choosesamplefields.route('/logSamples/parentid=<parentID>/chooseSampleFields/sampletype=<sampleType>', methods=['GET', 'POST'])
def choose_sample_fields(parentID,sampleType):
    '''
    Generate template html page code
    '''
    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

    setups = yaml.safe_load(open(os.path.join("website/templategenerator/website/config", "template_configurations.yaml"), encoding='utf-8'))['setups']

    config = 'Learnings from Nansen Legacy logging system'
    subconfig = 'default'
    for setup in setups:
        if setup['name'] == sampleType:
            subconfig = sampleType

    (
        output_config_dict,
        output_config_fields,
        extra_fields_dict,
        cf_standard_names,
        groups,
    ) = get_config_fields(config=config, subconfig=subconfig, CRUISE_NUMBER=CRUISE_NUMBER, DB=DB)
    # Creating a dictionary of all the fields.
    all_fields_dict = extra_fields_dict.copy()
    for key in output_config_dict.keys():
        for field, values in output_config_dict[key].items():
            all_fields_dict[field] = values

    #required_fields_dic, recommended_fields_dic, extra_fields_dic, groups = get_fields(configuration=config, CRUISE_NUMBER=CRUISE_NUMBER, DB=DB)
    #all_fields_dic = {**required_fields_dic, **recommended_fields_dic, **extra_fields_dic}

    most_likely_same_for_all_samples = [
    'parentID',
    'pi_details',
    'recordedBy_details',
    'sampleType',
    'gearType',
    'samplingProtocolDoc',
    'samplingProtocolSection',
    'samplingProtocolVersion'
    ]

    for key, val in output_config_dict['Required'].items():
        if key in most_likely_same_for_all_samples:
            val['checked'] = ['same']
        else:
            val['checked'] = ['vary']

    for key, val in output_config_dict['Recommended'].items():
        if key in most_likely_same_for_all_samples:
            val['checked'] = ['same']
        else:
            val['checked'] = ['vary']

    added_fields_dic = {}
    num_samples = 1
    current_setup = ''

    if request.method == 'POST':

        form_input = request.form.to_dict(flat=False)

        for key, val in form_input.items():
            if key not in output_config_fields and key != 'submitbutton':
                for field in fields.fields:
                    if field['name'] == key:
                        added_fields_dic[key] = {}
                        added_fields_dic[key]['disp_name'] = field['disp_name']
                        added_fields_dic[key]['description'] = field['description']

        for key, val in added_fields_dic.items():
            if key in most_likely_same_for_all_samples:
                val['checked'] = ['same']
            else:
                val['checked'] = ['vary']

        num_samples = int(form_input['num_samples'][0])

        if form_input['submitbutton'] == ['generateTemplate']:
            data_df = pd.DataFrame(index=np.arange(num_samples))
            for field, val in form_input.items():
                if field not in ['submitbutton','setupName','num_samples','userSetup']:
                    data_df[field] = ''
            data_df['parentID'] = parentID
            data_df['sampleType'] = sampleType

            gear_list = all_fields_dict['gearType']['source']
            if sampleType in gear_list:
                data_df['gearType'] = sampleType
            else:
                data_df['gearType'] = None

            #data_df = propegate_parents_to_children(data_df,DB,METADATA_CATALOGUE) # Should user get this information here for this in and out read?

            fields_list = list(set(list(output_config_dict['Required'].keys()) + list(data_df.columns)))

            filepath = f'/tmp/{CRUISE_NUMBER}_{sampleType}_parent{parentID}.xlsx'

            write_file(filepath, fields_list, metadata=True, conversions=True, data=data_df, metadata_df=False, DB=DB, CRUISE_DETAILS_TABLE=CRUISE_DETAILS_TABLE, METADATA_CATALOGUE=METADATA_CATALOGUE)

            return send_file(filepath, as_attachment=True)

        elif form_input['submitbutton'] == ['loadSetup']:

            current_setup = form_input['userSetup'][0]
            userSetup = get_user_setup(DB, current_setup) # json of setup

            # adding data for fields in setup to dictionaries to be displayed through HTML
            for key, val in userSetup.items():
                if '|' in val:
                    checked = val.split(' | ')
                else:
                    checked = [val]

                if key in output_config_dict['Required'].keys():
                    output_config_dict['Required'][key]['checked'] = checked
                if key in output_config_dict['Recommended'].keys():
                    output_config_dict['Recommended'][key]['checked'] = checked
                if key in extra_fields_dic.keys():
                    for field in fields.fields:
                        if field['name'] == key:
                            added_fields_dic[key] = {}
                            added_fields_dic[key]['disp_name'] = field['disp_name']
                            added_fields_dic[key]['description'] = field['description']
                            added_fields_dic[key]['checked'] = checked

            # Fields not included in setup shouldn't be checked.
            for key, val in output_config_dict['Recommended'].items():
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

            conn = psycopg2.connect(**DB)
            df = pd.read_sql(f'SELECT setupName FROM user_field_setups_{CRUISE_NUMBER};', con=conn)
            existing_user_setups = df['setupname'].tolist()

            if setupName in existing_user_setups and setupName != 'temporary':
                good = False
                errors.append(f'Setup with name {setupName} already exists. Please choose another name.')

            for key, val in form_input.items():
                if len(val) > 1:
                    good = False
                    errors.append(f'Can only tick one box per field: {key}')

            setup = {}

            for field in fields.fields:
                if field['name'] in form_input.keys() and form_input[field['name']] == ['y']:
                    pass
                else:
                    if field['name'] in form_input.keys():
                        sameorvary = form_input[field['name']] # "same" or "vary
                        if len(form_input[field['name']]) == 1:
                            setup[field['name']] = sameorvary[0]
                        else:
                            setup[field['name']] = " | ".join([str(item) for item in sameorvary])
                    else:
                        sameorvary = []
                        if field['name'] in output_config_dict['Required'].keys():
                            good = False
                            errors.append(f"At least one box must be ticked for all required fields: {field['disp_name']}")

                    if field['name'] in output_config_dict['Required'].keys():
                        output_config_dict['Required'][field['name']]['checked'] = sameorvary
                    elif field['name'] in output_config_dict['Recommended'].keys():
                        output_config_dict['Recommended'][field['name']]['checked'] = sameorvary
                    elif field['name'] in added_fields_dic.keys():
                        if field['name'] in form_input.keys():
                            added_fields_dic[field['name']]['checked'] = sameorvary
                        else:
                            added_fields_dic[field['name']]['checked'] = ['vary']

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

    if len(added_fields_dic) > 0:
        added_fields_bool = True
    else:
        added_fields_bool = False

    conn = psycopg2.connect(**DB)
    df = pd.read_sql(f"SELECT setupName FROM user_field_setups_{CRUISE_NUMBER} WHERE setupName != 'temporary';", con=conn)
    existing_user_setups = sorted(df['setupname'].tolist())


    return render_template(
    "chooseSampleFields.html",
    parentID=parentID,
    sampleType=sampleType,
    output_config_dict=output_config_dict,
    extra_fields_dic = extra_fields_dic,
    groups = groups,
    added_fields_dic = added_fields_dic,
    added_fields_bool = added_fields_bool,
    num_samples = num_samples,
    existing_user_setups = existing_user_setups,
    current_setup = current_setup
    )
