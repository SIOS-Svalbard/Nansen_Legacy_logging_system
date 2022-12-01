from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from website.spreadsheets.make_xlsx import write_file
#from website.spreadsheets.derive_metadata_df import derive_metadata_df
from website.database.get_data import get_data, get_cruise, get_personnel_df, get_samples_for_pi, get_samples_for_recordedby, get_samples_for_personnel, get_samples_for_sampletype
from website.other_functions.other_functions import split_personnel_list
from website.configurations.get_configurations import get_fields
from . import DB, METADATA_CATALOGUE, CRUISE_NUMBER
import website.database.fields as fields
import numpy as np
import yaml
import os

exportdata = Blueprint('exportdata', __name__)

@exportdata.route('/exportData', methods=['GET', 'POST'])
def export_data():

    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

    sample_types_df = get_data(DB, 'sample_types')
    sampleTypes = list(sample_types_df['sampletype'])

    personnel_df = get_personnel_df(DB=DB, table='personnel', CRUISE_NUMBER=CRUISE_NUMBER)
    personnel = list(personnel_df['personnel'])

    if request.method == 'POST':

        form_input = request.form.to_dict(flat=False)

        if form_input['selection'] == ['pi']:

            pi = form_input['personnel']

            pi_name, pi_email, pi_orcid, pi_institution = split_personnel_list(pi, personnel_df)

            df_to_export = get_samples_for_pi(DB, CRUISE_NUMBER, pi_email)

            filepath = f'/tmp/{CRUISE_NUMBER}_pi_{pi_name}.xlsx'

        if form_input['selection'] == ['recordedby']:

            recordedby = form_input['personnel']

            recordedby_name, recordedby_email, recordedby_orcid, recordedby_institution = split_personnel_list(recordedby, personnel_df)

            df_to_export = get_samples_for_recordedby(DB, CRUISE_NUMBER, recordedby_email)

            filepath = f'/tmp/{CRUISE_NUMBER}_recorded_by_{recordedby_name}.xlsx'

        if form_input['selection'] == ['piorrecordedby']:

            personnel = form_input['personnel']

            personnel_name, personnel_email, personnel_orcid, personnel_institution = split_personnel_list(personnel, personnel_df)

            df_to_export = get_samples_for_personnel(DB, CRUISE_NUMBER, personnel_email)

            filepath = f'/tmp/{CRUISE_NUMBER}_{personnel_name}.xlsx'

        if form_input['selection'] == ['sampleType']:

            sampletype = form_input['sampleType'][0]

            df_to_export = get_samples_for_sampletype(DB, CRUISE_NUMBER, sampletype)

            filepath = f'/tmp/{CRUISE_NUMBER}_{sampletype}.xlsx'

        # Creating new columns from the hstore key/value pairs in the 'other' column
        df_to_export = df_to_export.join(df_to_export['other'].str.extractall(r'\"(.+?)\"=>\"(.+?)\"')
             .reset_index()
             .pivot(index=['level_0', 'match'], columns=0, values=1)
             .groupby(level=0)
             .agg(lambda x: ''.join(x.dropna()))
             .replace('', np.nan)
             )

        # calculate metadata df where possible

        setups = yaml.safe_load(open(os.path.join("website/configurations", "template_configurations.yaml"), encoding='utf-8'))['setups']

        config = 'default'
        # for setup in setups:
        #     if setup['name'] == sampleType:
        #         config = sampleType
        required_fields_dic, recommended_fields_dic, extra_fields_dic, groups = get_fields(configuration=config, DB=DB, CRUISE_NUMBER=CRUISE_NUMBER)
        required = list(required_fields_dic.keys())

        df_to_export.replace('nan', np.nan, inplace=True)
        df_to_export.replace('NULL', np.nan, inplace=True)

        for field in fields.fields:
            # Column names come out of PSQL all lower case. Changing to make field names.
            if field['name'].lower() in df_to_export.columns and field['name'].lower() != field['name']:
                df_to_export.rename(columns = {field['name'].lower(): field['name']}, inplace=True)
            # Dropping non-required columns that are empty
            if field['name'] in df_to_export.columns and field['name'] not in required:
                if not df_to_export.loc[:, field['name']].notna().any():
                    df_to_export.drop([field['name']], axis=1, inplace=True)


        for col in ['created','modified','pi_details','recordedBy_details']:
            if col in df_to_export.columns:
                df_to_export.drop([col], axis=1, inplace=True)

        df_to_export.fillna('', inplace=True)

        #metadata_df = derive_metadata_df(df_to_export)
        metadata_df = False

        write_file(filepath, df_to_export.columns, metadata=True, conversions=True, data=df_to_export, metadata_df=False, DB=DB, CRUISE_NUMBER=CRUISE_NUMBER)

        return send_file(filepath, as_attachment=True)

    return render_template(
    "exportData.html",
    personnel=personnel,
    sampleTypes=sampleTypes
    )
