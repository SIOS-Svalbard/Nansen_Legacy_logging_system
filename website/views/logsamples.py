from flask import Blueprint, render_template, request, flash, redirect, url_for
import uuid
from website.lib.get_children_list_of_dics import get_children_list_of_dics
from website.lib.get_data import get_data, get_cruise, get_personnel_df, get_metadata_for_record_and_ancestors, get_metadata_for_id, get_metadata_for_list_of_ids
from website.lib.input_update_records import insert_into_metadata_catalogue, update_record_metadata_catalogue, update_record_metadata_catalogue_df
from website.lib.checker import run as checker
from website.lib.propegate_parents_to_children import find_all_children, propegate_parents_to_children
from website.lib.other_functions import split_personnel_list, combine_personnel_details, get_title, format_form_value
from website import DB, FIELDS_FILEPATH, CONFIG
import numpy as np
from datetime import datetime as dt
import pandas as pd
from math import isnan
from website.lib.get_setup_for_configuration import get_setup_for_configuration
from website.Learnings_from_AeN_template_generator.website.lib.get_configurations import get_list_of_subconfigs
from website.lib.get_dict_for_list_of_fields import get_dict_for_list_of_fields

logsamples = Blueprint('logsamples', __name__)

@logsamples.route('/editActivity/id=<ID>', methods=['GET'])
def edit_activity_page(ID):
    return render_template(
    "addActivity.html",
    ID=ID
    )

@logsamples.route('/editActivity/form/id=<ID>', methods=['GET', 'POST'])
def edit_activity_form(ID):

    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())
    subconfig = 'activity'
    list_of_subconfigs = get_list_of_subconfigs(config='Learnings from Nansen Legacy logging system')

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

    sample_metadata_df = get_metadata_for_id(DB, CRUISE_NUMBER, ID)

    # Creating new columns from the hstore key/value pairs in the 'other' column
    sample_metadata_df = sample_metadata_df.join(sample_metadata_df['other'].str.extractall(r'\"(.+?)\"=>\"(.+?)\"')
         .reset_index()
         .pivot(index=['level_0', 'match'], columns=0, values=1)
         .groupby(level=0)
         .agg(lambda x: ''.join(x.dropna()))
         .replace('', np.nan)
         )

    other_columns = []
    # Splitting hstore to get column names
    if len(sample_metadata_df) == 1:
        n = 0
        if sample_metadata_df['other'].item() != None:
            for a in sample_metadata_df['other'].item().split(', '): # Split fields with values from other fields with values
                for b in a.split('=>'): # Split fields from values
                    n = n + 1
                    if (n % 2) != 0: # Only append odd numbers, just the fields not the values
                        field_name = b[1:-1] # Removing first an last character, the quotation marks (")
                        other_columns.append(field_name)
                        if field_name != '':
                            for field in cf_standard_names:
                                if field['id'] == field_name:
                                    added_cf_names_dic['Data'][field['id']] = field['id']
                            for field in dwc_terms_not_in_config['Data']:
                                if field['id'] == field_name:
                                    added_dwc_terms_dic['Data'][field['id']] = field['id']
                            for field, vals in extra_fields_dict.items():
                                if field == field_name:
                                    added_fields_dic['Data'][field] = vals

    # Assigning values already registered in database for output_config_dict
    for sheet in output_config_dict.keys():
        for requirement in output_config_dict[sheet].keys():
            if requirement not in ['Required CSV', 'Source']:
                for field, vals in output_config_dict[sheet][requirement].items():
                    if ID == 'addNew':
                        if vals['format'] in ['double precision', 'date', 'time']:
                            output_config_dict[sheet][requirement][field]['value'] = None
                        else:
                            output_config_dict[sheet][requirement][field]['value'] = ''
                    else:
                        if field in other_columns:
                            output_config_dict[sheet][requirement][field]['value'] = sample_metadata_df[field].item()
                        elif field.lower() in sample_metadata_df.columns:
                            if field not in ['recordedBy', 'pi_details']:
                                output_config_dict[sheet][requirement][field]['value'] = sample_metadata_df[field.lower()].item()
                        else: # If not a column the field has not been logged
                            if vals['format'] in ['double precision', 'date', 'time']:
                                output_config_dict[sheet][requirement][field]['value'] = None
                            else:
                                output_config_dict[sheet][requirement][field]['value'] = ''

    if len(sample_metadata_df) == 1 and sample_metadata_df['pi_name'].item() not in ['', None]:
        output_config_dict['Data']['Required']['pi_details']['value'] = combine_personnel_details(sample_metadata_df['pi_name'].item(),sample_metadata_df['pi_email'].item())
    else:
        output_config_dict['Data']['Required']['pi_details']['value'] = []

    if len(sample_metadata_df) == 1 and sample_metadata_df['recordedby_name'].item() not in ['', None]:
        output_config_dict['Data']['Required']['recordedBy']['value'] = combine_personnel_details(sample_metadata_df['recordedby_name'].item(),sample_metadata_df['recordedby_email'].item())
    else:
        output_config_dict['Data']['Required']['recordedBy']['value'] = []

    # Assigning values already registered in database for dictionaries with added fields
    for field in cf_standard_names:
        for sheet in added_cf_names_dic.keys():
            if sheet not in ['Required CSV', 'Source']:
                if field['id'] in sample_metadata_df.columns and field['id'] not in output_config_fields:
                    if ID != 'addNew':
                        added_cf_names_dic[sheet][field['id']] = field
                        if field['id'] in other_columns:
                            added_cf_names_dic[sheet][field['id']]['value'] = sample_metadata_df[field['id']].item()
                        elif field['id'].lower() in sample_metadata_df.columns:
                            if field not in ['recordedBy', 'pi_details']:
                                added_cf_names_dic[sheet][field['id']]['value'] = sample_metadata_df[field['id'].lower()].item()
                        else: # If not a column the field has not been logged
                            if field['format'] in ['double precision', 'date', 'time']:
                                added_cf_names_dic[sheet][field['id']]['value'] = None
                            else:
                                added_cf_names_dic[sheet][field['id']]['value'] = ''

    for term in dwc_terms:
        for sheet in added_dwc_terms_dic.keys():
            if sheet not in ['Required CSV', 'Source']:
                if term['id'] in sample_metadata_df.columns and term['id'] not in output_config_fields:
                    if ID != 'addNew':
                        added_dwc_terms_dic[sheet][term['id']] = term
                        if term['id'] in other_columns:
                            added_dwc_terms_dic[sheet][term['id']]['value'] = sample_metadata_df[term['id']].item()
                        elif term['id'].lower() in sample_metadata_df.columns:
                            if term['id'] not in ['recordedBy', 'pi_details']:
                                added_dwc_terms_dic[sheet][term['id']]['value'] = sample_metadata_df[term['id'].lower()].item()
                        else: # If not a column the field has not been logged
                            if term['format'] in ['double precision', 'date', 'time']:
                                added_dwc_terms_dic[sheet][term['id']]['value'] = None
                            else:
                                added_dwc_terms_dic[sheet][term['id']]['value'] = ''

    for field, vals in extra_fields_dict.items():
        if field not in ['recordSource', 'history', 'modified', 'created']:
            for sheet in added_fields_dic.keys():
                if sheet not in ['Required CSV', 'Source']:
                    if vals['id'] in sample_metadata_df.columns and vals['id'] not in output_config_fields:
                        if ID != 'addNew':
                            added_fields_dic[sheet][vals['id']] = vals
                            if vals['id'] in other_columns:
                                value = sample_metadata_df[vals['id']].item()
                                if value not in [None, '']:
                                    added_fields_dic[sheet][vals['id']]['value'] = value
                                else:
                                    added_fields_dic[sheet].pop(vals['id'], None)
                            elif vals['id'].lower() in sample_metadata_df.columns:
                                if field not in ['recordedBy', 'pi_details']:
                                    value = sample_metadata_df[vals['id'].lower()].item()
                                    if value not in [None, '']:
                                        added_fields_dic[sheet][vals['id']]['value'] = sample_metadata_df[vals['id'].lower()].item()
                                    else:
                                        added_fields_dic[sheet].pop(vals['id'], None)
                            else: # If not a column the field has not been logged
                                if vals['format'] in ['double precision', 'date', 'time']:
                                    added_fields_dic[sheet][vals['id']]['value'] = None
                                else:
                                    added_fields_dic[sheet][vals['id']]['value'] = ''

    # Get children
    if ID != 'addNew':
        ids = [ID]
        children_list_of_dics = get_children_list_of_dics(DB, CRUISE_NUMBER, FIELDS_FILEPATH, ids)
    else:
        children_list_of_dics = []

    if request.method == 'POST':

        form_input = request.form.to_dict(flat=False)
        all_form_keys = request.form.keys()

        # 1. Preserve the values added in the form for each field by adding them to the relevant dictionaries
        for sheet in output_config_dict.keys():
            for requirement in output_config_dict[sheet].keys():
                if requirement not in ['Required CSV', 'Source']:
                    for field, vals in output_config_dict[sheet][requirement].items():
                        if field in form_input:
                            vals['value'] = form_input[field] = format_form_value(field, form_input[field], vals['format'])
                        else:
                            if field in ['pi_details', 'recordedBy']:
                                vals['value'] = []

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
                            added_cf_names_dic[sheet][field['id']]['value'] = form_input[form_key] = format_form_value(field['id'], form_input[form_key], field['format'])

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
                        added_dwc_terms_dic[sheet][term['id']]['value'] = form_input[form_key] = format_form_value(term['id'], form_input[form_key], term['format'])

        # Other fields (not CF standard names or DwC terms - terms designed for the template generator and logging system)
        for field, vals in extra_fields_dict.items():
            for form_key in all_form_keys:
                if field == form_key:
                    added_fields_dic['Data'][field] = vals
                    added_fields_dic['Data'][field]['value'] = form_input[form_key] = format_form_value(field, form_input[form_key], vals['format'])

        if request.form['submitbutton'] == 'submit':

            df_personnel = get_personnel_df(DB=DB, CRUISE_NUMBER=CRUISE_NUMBER, table='personnel')
            if 'pi_details' in form_input.keys():
                form_input['pi_name'], form_input['pi_email'], form_input['pi_orcid'], form_input['pi_institution'] = split_personnel_list(form_input['pi_details'], df_personnel)
            else:
                form_input['pi_name'] = form_input['pi_email'] = form_input['pi_orcid'] = form_input['pi_institution'] = ''
            if 'recordedBy' in form_input.keys():
                form_input['recordedBy_name'], form_input['recordedBy_email'], form_input['recordedBy_orcid'], form_input['recordedBy_institution'] = split_personnel_list(form_input['recordedBy'], df_personnel)
            else:
                form_input['recordedBy_name'] = form_input['recordedBy_email'] = form_input['recordedBy_orcid'] = form_input['recordedBy_institution'] = ''

            for key in ['pi_details', 'recordedBy', 'submitbutton']:
                if key in form_input.keys():
                    form_input.pop(key)

            fields_to_check_dic = {}
            for key, val in form_input.items():
                fields_to_check_dic[key] = [val]
            fields_to_check_df = pd.DataFrame.from_dict(fields_to_check_dic)

            for col in ['eventTime', 'endTime', 'middleTime']:
                if col in fields_to_check_df.columns:
                    fields_to_check_df[col] = pd.to_datetime(fields_to_check_df[col])
            for col in ['eventDate','endDate', 'middleDate']:
                if col in fields_to_check_df.columns:
                    fields_to_check_df[col] = pd.to_datetime(fields_to_check_df[col])

            if ID == 'addNew':
                new = True
            else:
                new = False

            required = list(output_config_dict['Data']['Required'].keys())
            if 'pi_details' in required:
                required.remove('pi_details')
                required = required + ['pi_name', 'pi_email', 'pi_orcid', 'pi_institution']
            if 'recordedBy' in required:
                required.remove('recordedBy')
                required = required + ['recordedBy_name', 'recordedBy_email', 'recordedBy_orcid', 'recordedBy_institution']

            good, errors = checker(
                data=fields_to_check_df,
                required=required,
                DB=DB,
                CRUISE_NUMBER=CRUISE_NUMBER,
                new=new,
                old_id=ID
                )

            if good == False:
                for error in errors:
                    flash(error, category='error')

            else:

                fields_to_submit = {} # dictionary to populate with with fields, values and formatting requirements to submit to metadata catalogue table in database
                fields_to_submit['columns'] = {}
                fields_to_submit['hstore'] = {}
                metadata_columns_list = CONFIG["metadata_catalogue"]["fields_to_use_as_columns"]

                for sheet in output_config_dict.keys():
                    for requirement in output_config_dict[sheet].keys():
                        if requirement not in ['Required CSV', 'Source']:
                            for field, vals in output_config_dict[sheet][requirement].items():
                                if field in form_input:
                                    if form_input[field] == '':
                                        if output_config_dict[sheet][requirement][field]['format'] in ['int', 'double precision', 'time', 'date']:
                                            output_config_dict[sheet][requirement][field]['value'] = 'NULL'
                                        elif field == 'id':
                                            output_config_dict[sheet][requirement][field]['value'] = str(uuid.uuid4())
                                    if field in metadata_columns_list:
                                        fields_to_submit['columns'][field] = output_config_dict[sheet][requirement][field]
                                    else:
                                        fields_to_submit['hstore'][field] = output_config_dict[sheet][requirement][field]

                fields_to_submit['hstore']['eventID'] = fields_to_submit['columns']['id']

                personnel_fields_list = ['pi_name', 'pi_email', 'pi_orcid', 'pi_institution', 'recordedBy_name', 'recordedBy_email', 'recordedBy_email', 'recordedBy_institution']
                personnel_fields_dict = get_dict_for_list_of_fields(personnel_fields_list,FIELDS_FILEPATH)
                for field in personnel_fields_list:
                    fields_to_submit['columns'][field] = personnel_fields_dict[field]
                    fields_to_submit['columns'][field]['value'] = form_input[field]

                for sheet in added_cf_names_dic.keys():
                    for field, vals in added_cf_names_dic[sheet].items():
                        if field in metadata_columns_list:
                            fields_to_submit['columns'][field] = added_cf_names_dic[sheet][field]
                        else:
                            fields_to_submit['hstore'][field] = added_cf_names_dic[sheet][field]

                for sheet in added_dwc_terms_dic.keys():
                    for term, vals in added_dwc_terms_dic[sheet].items():
                        if term in metadata_columns_list:
                            fields_to_submit['columns'][term] = added_dwc_terms_dic[sheet][term]
                        else:
                            fields_to_submit['hstore'][term] = added_dwc_terms_dic[sheet][term]

                for sheet in added_fields_dic.keys():
                    for field, vals in added_fields_dic[sheet].items():
                        if field in metadata_columns_list:
                            fields_to_submit['columns'][field] = added_fields_dic[sheet][field]
                        else:
                            fields_to_submit['hstore'][field] = added_fields_dic[sheet][field]

                record_details = get_dict_for_list_of_fields(['created','modified','history','recordSource'],FIELDS_FILEPATH)
                fields_to_submit['columns']['created'] = record_details['created']
                fields_to_submit['columns']['modified'] = record_details['modified']
                fields_to_submit['columns']['history'] = record_details['history']
                fields_to_submit['columns']['recordSource'] = record_details['recordSource']

                if ID == 'addNew':

                    fields_to_submit['columns']['created']['value'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                    fields_to_submit['columns']['modified']['value'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                    fields_to_submit['columns']['history']['value'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record created manually from add activity page")
                    fields_to_submit['columns']['recordSource']['value'] = "Record created manually from add activity page"

                    insert_into_metadata_catalogue(fields_to_submit, 1, DB, CRUISE_NUMBER)

                    flash('Activity registered!', category='success')

                else:

                    fields_to_submit['columns']['modified']['value'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                    fields_to_submit['columns']['history']['value'] = sample_metadata_df.loc[sample_metadata_df['id'] == ID, 'history'].iloc[0]
                    fields_to_submit['columns']['history']['value'] = fields_to_submit['columns']['history']['value'] + '\n' + dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record modified using edit activity page")

                    update_record_metadata_catalogue(fields_to_submit, DB, CRUISE_NUMBER, ID)

                    flash('Activity edited!', category='success')
                    #
                    # children_IDs = find_all_children([ID],DB, CRUISE_NUMBER)
                    # if len(children_IDs) > 0:
                    #     df_children = get_metadata_for_list_of_ids(DB, METADATA_CATALOGUE, children_IDs)
                    #     df_children = propegate_parents_to_children(df_children,DB, METADATA_CATALOGUE)
                    #     df_children = df_children.replace(to_replace=['None', None, 'nan'],value='NULL')
                    #     metadata_df = False
                    #     update_record_metadata_catalogue_df(df_children, metadata_df, DB, CRUISE_NUMBER)
                    #
                    #     flash('Relevant metadata copied to children', category='success')

                return redirect('/')

    if ID == 'addNew':
        ID = None
        trace = pd.DataFrame()
    else:
        trace = get_metadata_for_record_and_ancestors(DB, CRUISE_NUMBER, ID)

    return render_template(
    "addActivityForm.html",
    ID=ID,
    output_config_dict=output_config_dict,
    extra_fields_dict=extra_fields_dict,
    groups=groups,
    added_fields_dic=added_fields_dic,
    cf_standard_names=cf_standard_names,
    added_cf_names_dic=added_cf_names_dic,
    dwc_terms_not_in_config=dwc_terms_not_in_config,
    added_dwc_terms_dic=added_dwc_terms_dic,
    list_of_subconfigs=list_of_subconfigs,
    subconfig=subconfig,
    trace=trace,
    children_list_of_dics=children_list_of_dics,
    len=len,
    isnan=isnan,
    get_title=get_title
    )

@logsamples.route('/logSamples/parentid=<ID>', methods=['GET', 'POST'])
def log_samples(ID):

    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

    # Get children
    if ID != 'addNew':
        ids = [ID]
        children_list_of_dics = get_children_list_of_dics(DB, CRUISE_NUMBER, FIELDS_FILEPATH, ids)
    else:
        children_list_of_dics = []

    sample_types_df = get_data(DB, 'sampletype')
    gear_types_df = get_data(DB, 'geartype')

    sample_metadata_df = get_metadata_for_id(DB, CRUISE_NUMBER, ID)
    gearType = sample_metadata_df['geartype'].item()

    recommendedChildSamples = find_recommended_child_sample_types(gearType, gear_types_df)

    return render_template(
    "logSamples.html",
    ID=ID,
    recommendedChildSamples=recommendedChildSamples,
    children_list_of_dics=children_list_of_dics,
    sample_types_df=sample_types_df,
    trace=get_metadata_for_record_and_ancestors(DB, CRUISE_NUMBER, ID),
    len=len,
    isnan=isnan,
    get_title=get_title,
    )

def find_recommended_child_gears(gearType, gear_types_df):

    series = gear_types_df.loc[gear_types_df['geartype'] == gearType, 'recommendedchildgears']

    if len(series) == 0:
        recommended_child_gears = ""
    else:
        recommended_child_gears = series.item()

    if recommended_child_gears == "":
        recommended_child_gears_list = []
    else:
        recommended_child_gears_list = recommended_child_gears.split(', ')
    return recommended_child_gears_list

def find_recommended_child_sample_types(gearType, gear_types_df):

    series = gear_types_df.loc[gear_types_df['geartype'] == gearType, 'recommendedchildsamples']
    if len(series) == 0 or list(series) == ['nan']:
        recommended_child_samples = ""
    else:
        recommended_child_samples = series.item()

    if recommended_child_samples == "":
        recommended_child_samples_list = []
    else:
        recommended_child_samples_list = recommended_child_samples.split(', ')

    return recommended_child_samples_list
