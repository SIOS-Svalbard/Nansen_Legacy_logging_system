from flask import Blueprint, render_template, request, send_file
from website.lib.get_data import get_data, get_cruise, get_personnel_df, get_samples_for_pi, get_samples_for_recordedby, get_samples_for_personnel, get_samples_for_sampletype
from website.lib.other_functions import split_personnel_list
from website import DB, FIELDS_FILEPATH
import numpy as np
import yaml
import os
from website.lib.other_functions import combine_fields_dictionaries
from website.Learnings_from_AeN_template_generator.website.lib.create_template import create_template
from website.Learnings_from_AeN_template_generator.website.lib.get_configurations import get_list_of_subconfigs
from website.lib.get_setup_for_configuration import get_setup_for_configuration
from website.lib.get_dict_for_list_of_fields import get_dict_for_list_of_fields

exportdata = Blueprint('exportdata', __name__)

@exportdata.route('/exportData', methods=['GET', 'POST'])
def export_data():

    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

    sample_types_df = get_data(DB, 'sampletype')
    sampleTypes = list(sample_types_df['sampletype'])
    sampleType = None

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

            sampleType = form_input['sampleType'][0]

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

        config = 'Learnings from Nansen Legacy logging system'
        list_of_subconfigs = get_list_of_subconfigs(config=config)

        if sampleType in list_of_subconfigs:
            subconfig = sampleType
        else:
            subconfig = 'activity'
        
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

        # config_dict = get_config_fields_dic(config=config, subconfig=subconfig)
        required = output_config_dict['Data']['Required'].keys()
        required_lower = [r.lower() for r in required]

        df_to_export.replace('nan', np.nan, inplace=True)
        df_to_export.replace('NULL', np.nan, inplace=True)

        for requirement in output_config_dict['Data'].keys():
            if requirement not in ['Required CSV', 'Source']:
                for field, vals in output_config_dict['Data'][requirement].items():
                    # Column names come out of PSQL all lower case. Changing to make field names.
                    if field.lower() in df_to_export.columns and field.lower() != field:
                        df_to_export.rename(columns = {field.lower(): field}, inplace=True)
                    # Dropping non-required columns that are empty
                    if field in df_to_export.columns and requirement != 'Required':
                        if not df_to_export.loc[:, field].notna().any():
                            df_to_export.drop([field], axis=1, inplace=True)

        for col in ['created','modified','pi_details','recordedBy']:
            if col in df_to_export.columns:
                df_to_export.drop([col], axis=1, inplace=True)

        df_to_export.fillna('', inplace=True)

        personnel_details_dict = get_dict_for_list_of_fields(['recordedBy_name', 'recordedBy_email', 'recordedBy_orcid', 'recordedBy_institution', 'pi_name', 'pi_email', 'pi_orcid', 'pi_institution'],FIELDS_FILEPATH)
        for field, vals in personnel_details_dict.items():
            output_config_dict['Data']['Required'][field] = vals

        output_config_dict['Data']['Required'].pop('pi_details', None)
        output_config_dict['Data']['Required'].pop('recordedBy', None)

        template_fields_dict = combine_fields_dictionaries(
            output_config_dict,
            added_fields_dic,
            added_cf_names_dic,
            added_dwc_terms_dic,
            df_to_export
        )

        # NEED TO REMOVE PI_DETAILS AND RECORDED_BY AND ADD SEPARATED TERMS TO TEMPLATE_FIELDS_DICT BUT HOW?

        create_template(
            filepath = filepath,
            template_fields_dict = template_fields_dict,
            fields_filepath = FIELDS_FILEPATH,
            config = config,
            subconfig=subconfig,
            metadata=True,
            conversions=True,
            split_personnel_columns=False
        )

        return send_file(filepath, as_attachment=True)

    return render_template(
    "exportData.html",
    personnel=personnel,
    sampleTypes=sampleTypes
    )
