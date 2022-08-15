from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
import psycopg2
import psycopg2.extras
import getpass
import uuid
from website.database.get_data import get_data
from website.database.input_update_records import insert_into_metadata_catalogue, update_record_metadata_catalogue
from website.database.harvest_activities import harvest_activities, get_bottom_depth
from website.database.checker import run as checker
import website.database.fields as fields
from website.spreadsheets.make_xlsx import write_file
from website.other_functions.other_functions import distanceCoordinates, split_personnel_list
from . import DBNAME, CRUISE_NUMBER, METADATA_CATALOGUE, CRUISE_DETAILS_TABLE, VESSEL_NAME, TOKTLOGGER
import requests
import numpy as np
from datetime import datetime as dt
import pandas as pd
import yaml
import os

generatetemplates = Blueprint('generatetemplates', __name__)

@generatetemplates.route('/generateTemplate', methods=['GET', 'POST'])
def generate_template():

    setups = yaml.safe_load(open(os.path.join("website/configurations", "template_configurations.yaml"), encoding='utf-8'))['setups']

    for setup in setups:
        if setup['name'] == 'activity':
            required_fields = setup['fields']['required']
            recommended_fields = setup['fields']['recommended']

    required_fields_dic = {}
    recommended_fields_dic = {}
    extra_fields_dic = {}

    groups = []
    extrafields=[]

    for field in fields.fields:
        if field['name'] in required_fields:
            required_fields_dic[field['name']] = {}
            required_fields_dic[field['name']]['disp_name'] = field['disp_name']
            required_fields_dic[field['name']]['description'] = field['description']
        elif field['name'] in recommended_fields:
            recommended_fields_dic[field['name']] = {}
            recommended_fields_dic[field['name']]['disp_name'] = field['disp_name']
            recommended_fields_dic[field['name']]['description'] = field['description']
        else:
            # Setting up the 'modal' where the user can add more fields
            # Removing fields already included on the form and creating a list of groups so they can be grouped on the UI.
            if field['grouping'] not in ['Record Details', 'ID', 'Cruise Details'] and field['name'] not in ['pi_name', 'pi_email', 'pi_institution', 'recordedBy_name', 'recordedBy_email', 'recordedBy_institution']:
                extrafields.append(field)
                groups.append(field['grouping'])

    groups = sorted(list(set(groups)))

    if 'pis' in required_fields:
        required_fields_dic['pi_details'] = {
            'disp_name': 'PI Details',
            'description': 'Full name(s), email(s) and instituion(s) of the principal investigator(s) of the data'
            }
    elif 'pis' in recommended_fields:
        recommended_fields_dic['pi_details'] = {
            'disp_name': 'PI Details',
            'description': 'Full name(s), email(s) and instituion(s) of the principal investigator(s) of the data'
            }

    if 'recordedBys' in required_fields:
        required_fields_dic['recordedBy_details'] = {
            'disp_name': 'Recorded By',
            'description': 'Full name(s), email(s) and instituion(s) of the people who have recorded/analysed the data'
            }
    elif 'recordedBys' in recommended_fields:
        recommended_fields_dic['recordedBy_details'] = {
            'disp_name': 'Recorded By',
            'description': 'Full name(s), email(s) and instituion(s) of the people who have recorded/analysed the data'
            }

    if request.method == 'POST':

        form_input = request.form.to_dict(flat=False)

        for key, val in form_input.items():
            if key not in required_fields and key not in recommended_fields and key != 'submitbutton':
                for field in fields.fields:
                    if field['name'] == key:
                        extra_fields_dic[key] = {}
                        extra_fields_dic[key]['disp_name'] = field['disp_name']
                        extra_fields_dic[key]['description'] = field['description']

        if form_input['submitbutton'] == ['generateTemplate']:

            fields_list = required_fields

            for field, val in form_input.items():
                if val == ['on']:
                    fields_list = fields_list + [field]

            filepath = '/tmp/generated_template.xlsx'

            write_file(filepath, fields_list, metadata=False, conversions=True, data=False, metadata_df=False)

            return send_file(filepath, as_attachment=True)

    if len(extra_fields_dic) > 0:
        extra_fields_bool = True
    else:
        extra_fields_bool = False

    return render_template(
    "generateTemplate.html",
    required_fields_dic = required_fields_dic,
    recommended_fields_dic = recommended_fields_dic,
    extra_fields_dic = extra_fields_dic,
    fields=extrafields,
    groups=groups,
    extra_fields_bool=extra_fields_bool
    )
