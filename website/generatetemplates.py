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
from website.configurations.get_configurations import get_fields
from website.spreadsheets.make_xlsx import write_file
from website.other_functions.other_functions import distanceCoordinates, split_personnel_list
from . import DBNAME, CRUISE_NUMBER, METADATA_CATALOGUE, CRUISE_DETAILS_TABLE, VESSEL_NAME, TOKTLOGGER
import requests
import numpy as np
from datetime import datetime as dt
import pandas as pd
import os

generatetemplates = Blueprint('generatetemplates', __name__)

@generatetemplates.route('/generateTemplate', methods=['GET', 'POST'])
def generate_template():
    '''
    Generate template html page code
    '''
    required_fields_dic, recommended_fields_dic, extra_fields_dic, groups = get_fields(configuration='activity', DBNAME=DBNAME)

    added_fields_dic = {}
    if request.method == 'POST':

        form_input = request.form.to_dict(flat=False)

        for key, val in form_input.items():
            if key not in required_fields_dic.keys() and key not in recommended_fields_dic.keys() and key != 'submitbutton':
                for field in fields.fields:
                    if field['name'] == key:
                        added_fields_dic[key] = {}
                        added_fields_dic[key]['disp_name'] = field['disp_name']
                        added_fields_dic[key]['description'] = field['description']

        if form_input['submitbutton'] == ['generateTemplate']:

            fields_list = list(required_fields_dic.keys())

            for field, val in form_input.items():
                if val == ['on']:
                    fields_list = fields_list + [field]

            filepath = '/tmp/generated_template.xlsx'

            write_file(filepath, fields_list, metadata=True, conversions=True, data=False, metadata_df=False, DBNAME=DBNAME, CRUISE_DETAILS_TABLE=CRUISE_DETAILS_TABLE, METADATA_CATALOGUE=METADATA_CATALOGUE)

            return send_file(filepath, as_attachment=True)

    if len(added_fields_dic) > 0:
        added_fields_bool = True
    else:
        added_fields_bool = False

    return render_template(
    "generateTemplate.html",
    required_fields_dic = required_fields_dic,
    recommended_fields_dic = recommended_fields_dic,
    extra_fields_dic = extra_fields_dic,
    groups = groups,
    added_fields_dic = added_fields_dic,
    added_fields_bool = added_fields_bool
    )
