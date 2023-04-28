from flask import Blueprint, render_template, request, flash, redirect, url_for
import uuid
from website.lib.get_children_list_of_dics import get_children_list_of_dics
from website.lib.get_data import get_data, get_cruise, get_personnel_df, get_metadata_for_record_and_ancestors, get_metadata_for_id, get_metadata_for_list_of_ids
from website.lib.input_update_records import insert_into_metadata_catalogue, update_record_metadata_catalogue, update_record_metadata_catalogue_df
from website.lib.checker import run as checker
from website.lib.propegate_parents_to_children import find_all_children, propegate_parents_to_children
from website.lib.other_functions import split_personnel_list, combine_personnel_details, get_title
from website import DB
import numpy as np
from datetime import datetime as dt
import pandas as pd
from math import isnan

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

    required_fields_dic, recommended_fields_dic, extra_fields_dic, groups = get_fields(configuration='activity', DB=DB, CRUISE_NUMBER=CRUISE_NUMBER)

    activity_fields = {**required_fields_dic, **recommended_fields_dic} # Merging dictionarys

    required = list(required_fields_dic.keys())
    recommended = list(recommended_fields_dic.keys())

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
                            activity_fields[field_name] = extra_fields_dic[field_name]

    for field in fields.fields:
        if field['name'] in activity_fields.keys():
            if field['name'] in required:
                activity_fields[field['name']]['required'] = True
            else:
                activity_fields[field['name']]['required'] = False
            if ID == 'addNew':
                if field['format'] in ['double precision', 'date', 'time']:
                    activity_fields[field['name']]['value'] = None
                else:
                    activity_fields[field['name']]['value'] = ''
            else:
                if field['name'] in other_columns:
                    activity_fields[field['name']]['value'] = sample_metadata_df[field['name']].item()
                else:
                    if field['name'] not in ['recordedBy_details', 'pi_details']:
                        activity_fields[field['name']]['value'] = sample_metadata_df[field['name'].lower()].item()

    if len(sample_metadata_df) == 1 and sample_metadata_df['pi_name'].item() not in ['', None]:
        activity_fields['pi_details']['value'] = combine_personnel_details(sample_metadata_df['pi_name'].item(),sample_metadata_df['pi_email'].item())
    else:
        activity_fields['pi_details']['value'] = []

    if len(sample_metadata_df) == 1 and sample_metadata_df['recordedby_name'].item() not in ['', None]:
        activity_fields['recordedBy_details']['value'] = combine_personnel_details(sample_metadata_df['recordedby_name'].item(),sample_metadata_df['recordedby_email'].item())
    else:
        activity_fields['recordedBy_details']['value'] = []

    # Get children
    if ID != 'addNew':
        ids = [ID]
        children_list_of_dics = get_children_list_of_dics(DB, CRUISE_NUMBER, ids)
    else:
        children_list_of_dics = []

    if request.method == 'POST':

        form_input = request.form.to_dict(flat=False)

        for key, value in form_input.items():
            # Required fields already included by default
            if key in required or key in recommended:
                if len(value) == 1 and key not in ['pi_details', 'recordedBy_details']:
                    form_input[key] = value[0]
                    activity_fields[key]['value'] = value[0]
                elif key == 'pi_details':
                    activity_fields[key]['value'] = value
                elif key == 'recordedBy_details':
                    activity_fields[key]['value'] = value
                elif len(value) == 0:
                    form_input[key] = ''
                    activity_fields[key]['value'] = ''

            # Additional optional fields added by user
            elif value not in [['submit'],['addfields']]:
                activity_fields[key] = {}
                for field, field_info in extra_fields_dic.items():
                    if field == key:
                        activity_fields[key] = extra_fields_dic[key]
                        # First POST request is when user clicks 'add fields', and value of 'y' assigned as value for all fields with checked boxes
                        if value == ['y']:
                            if field_info['format'] in ['double precision', 'date', 'time']:
                                activity_fields[key]['value'] = None
                            else:
                                activity_fields[key]['value'] = ''

                        # Not first POST request, in cases where a field has been added and then need to redisplay, e.g. error on first load.
                        else:
                            if len(value) == 1:
                                form_input[key] = value[0]
                                activity_fields[key]['value'] = value[0]
                            elif len(value) == 0:
                                form_input[key] = ''
                                activity_fields[key]['value'] = ''

        if request.form['submitbutton'] == 'submit':

            df_personnel = get_personnel_df(DB=DB, CRUISE_NUMBER=CRUISE_NUMBER, table='personnel')
            if 'pi_details' in form_input.keys():
                form_input['pi_name'], form_input['pi_email'], form_input['pi_orcid'], form_input['pi_institution'] = split_personnel_list(form_input['pi_details'], df_personnel)
            else:
                form_input['pi_name'] = form_input['pi_email'] = form_input['pi_orcid'] = form_input['pi_institution'] = ''
            if 'recordedBy_details' in form_input.keys():
                form_input['recordedBy_name'], form_input['recordedBy_email'], form_input['recordedBy_orcid'], form_input['recordedBy_institution'] = split_personnel_list(form_input['recordedBy_details'], df_personnel)
            else:
                form_input['recordedBy_name'] = form_input['recordedBy_email'] = form_input['recordedBy_orcid'] = form_input['recordedBy_institution'] = ''

            for key in ['pi_details', 'recordedBy_details', 'submitbutton']:
                if key in form_input.keys():
                    form_input.pop(key)

            fields_to_check_dic = {}
            for key, val in form_input.items():
                fields_to_check_dic[key] = [val]
                fields_to_check_df = pd.DataFrame.from_dict(fields_to_check_dic)

            for col in ['eventTime', 'endTime']:
                if col in fields_to_check_df.columns:
                    fields_to_check_df[col] = pd.to_datetime(fields_to_check_df[col])
            for col in ['eventDate','endDate']:
                if col in fields_to_check_df.columns:
                    fields_to_check_df[col] = pd.to_datetime(fields_to_check_df[col])

            if ID == 'addNew':
                new = True
            else:
                new = False

            if 'pi_details' in required:
                required.remove('pi_details')
                required = required + ['pi_name', 'pi_email', 'pi_orcid', 'pi_institution']
            if 'recordedBy_details' in required:
                required.remove('recordedBy_details')
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
                for field in fields.fields:
                    if field['name'] in required or field['name'] in recommended:
                        if form_input[field['name']] == '':
                            if field['format'] in ['int', 'double precision', 'time', 'date']:
                                form_input[field['name']] = 'NULL'
                            elif field['name'] == 'id':
                                form_input[field['name']] = str(uuid.uuid1())

                form_input['eventID'] = form_input['id']

                if ID == 'addNew':

                    form_input['created'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                    form_input['modified'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                    form_input['history'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record created manually from add activity page")
                    form_input['source'] = "Record created manually from add activity page"

                    insert_into_metadata_catalogue(form_input, DB, CRUISE_NUMBER)

                    flash('Activity registered!', category='success')

                else:

                    form_input['history'] = sample_metadata_df.loc[sample_metadata_df['id'] == ID, 'history'].iloc[0]
                    form_input['history'] = form_input['history'] + '\n' + dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Record modified using edit activity page")
                    form_input['modified'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

                    update_record_metadata_catalogue(form_input, DB, CRUISE_NUMBER, ID)

                    flash('Activity edited!', category='success')

                    children_IDs = find_all_children([ID],DB, CRUISE_NUMBER)
                    if len(children_IDs) > 0:
                        df_children = get_metadata_for_list_of_ids(DB, METADATA_CATALOGUE, children_IDs)
                        df_children = propegate_parents_to_children(df_children,DB, METADATA_CATALOGUE)
                        df_children = df_children.replace(to_replace=['None', None, 'nan'],value='NULL')
                        metadata_df = False
                        update_record_metadata_catalogue_df(df_children, metadata_df, DB, CRUISE_NUMBER)

                        flash('Relevant metadata copied to children', category='success')

                return redirect(url_for('views.home'))

    if ID == 'addNew':
        ID = ''

    # Reordering dictionary to order in fields.py
    activity_metadata = {}
    for field in fields.fields:
        if field['name'] in activity_fields.keys():
            activity_metadata[field['name']] = activity_fields[field['name']]

    return render_template(
    "addActivityForm.html",
    ID=ID,
    activity_metadata=activity_metadata,
    extra_fields_dic=extra_fields_dic,
    groups=groups,
    trace=get_metadata_for_record_and_ancestors(DB, CRUISE_NUMBER, ID),
    children_list_of_dics=children_list_of_dics,
    len=len,
    isnan=isnan,
    get_title=get_title,
    )

@logsamples.route('/logSamples/parentid=<ID>', methods=['GET', 'POST'])
def log_samples(ID):

    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

    # Get children
    if ID != 'addNew':
        ids = [ID]
        children_list_of_dics = get_children_list_of_dics(DB, CRUISE_NUMBER, ids)
    else:
        children_list_of_dics = []

    sample_types_df = get_data(DB, 'sample_types')
    gear_types_df = get_data(DB, 'gear_types')

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
    if len(series) == 0:
        recommended_child_samples = ""
    else:
        recommended_child_samples = series.item()

    if recommended_child_samples == "":
        recommended_child_samples_list = []
    else:
        recommended_child_samples_list = recommended_child_samples.split(', ')

    return recommended_child_samples_list
