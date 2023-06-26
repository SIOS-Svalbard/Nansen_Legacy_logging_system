from flask import Blueprint, render_template, request, flash, redirect, url_for
from website.lib.get_data import get_personnel_df, get_cruise, get_metadata_for_list_of_ids, get_registered_niskins
from website.lib.input_update_records import update_record_metadata_catalogue
from website.lib.harvest_activities import harvest_activities
from website.lib.checker import run as checker
from website.lib.other_functions import split_personnel_list, combine_personnel_details, format_form_value
from website import DB, TOKTLOGGER, FIELDS_FILEPATH, CONFIG
from datetime import datetime as dt
from math import isnan
from website.lib.get_setup_for_configuration import get_setup_for_configuration
from website.lib.get_dict_for_list_of_fields import get_dict_for_list_of_fields
from website.lib.propegate_parents_to_children import propegate_parents_to_children

missingmetadata = Blueprint('missingmetadata', __name__)

def get_missing_activities():
    '''
    Get a dataframe of missing activities
    And a dictionary with the configuration for the required fields
    '''
    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

    activities_df = harvest_activities(TOKTLOGGER, DB, CRUISE_NUMBER).reset_index()

    # Loading fields
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
        subconfig='Activities',
        CRUISE_NUMBER=CRUISE_NUMBER
    )

    # Removing rows from dataframe where no missing values

    # Checking rows logged without either depth NOR elevation (only one required)
    # Minimum and maximum both required

    # If min or max depth missing, depths_recorded = False
    if 'minimumDepthInMeters' in output_config_dict['Data']['Recommended'].keys() and 'maximumDepthInMeters' in output_config_dict['Data']['Recommended'].keys():
        activities_df['depths_recorded'] = ~activities_df[['minimumdepthinmeters','maximumdepthinmeters']].isna().any(axis = 1)
    else:
        activities_df['depths_recorded'] = True # So rows are not dropped later based on depth
    # If min or max elevation missing, elevations_recorded = False
    if 'minimumElevationInMeters' in output_config_dict['Data']['Recommended'].keys() and 'maximumElevationInMeters' in output_config_dict['Data']['Recommended'].keys():
        activities_df['elevations_recorded'] = ~activities_df[['minimumelevationinmeters','maximumelevationinmeters']].isna().any(axis = 1)
    else:
        activities_df['elevations_recorded'] = True # So rows are not dropped later based on depth# If depths_recorded is True or elevations_recorded is True, then it okay.
    # So keep if both are False

    # Other fields
    check_for_missing = list(output_config_dict['Data']['Required'].keys())
    check_for_missing = [c.lower() for c in check_for_missing]
    if 'pi_details' in check_for_missing:
        check_for_missing.remove('pi_details')
        check_for_missing = check_for_missing + ['pi_name', 'pi_email', 'pi_institution']
    if 'recordedby' in check_for_missing:
        check_for_missing.remove('recordedby')
        check_for_missing = check_for_missing + ['recordedby_name', 'recordedby_email', 'recordedby_institution']

    # If any required columns are missing, then 'all_required_present' = False
    activities_df['all_required_present'] = ~activities_df[check_for_missing].isna().any(axis = 1)

    # Keep all rows where all required_present is False AND
    # EITHER depths recorded is False OR elevations recorded is False
    activities_df = activities_df[(activities_df['all_required_present'] == False) | (activities_df['depths_recorded'] == False) & (activities_df['elevations_recorded'] == False)]

    # Sorting dataframe
    activities_df.sort_values(by=['eventdate', 'eventtime'], ascending=False, inplace=True)
    activities_df = activities_df.reset_index()

    return activities_df, output_config_dict

def get_missing_niskins():
    '''
    Get a dataframe of missing activities
    And a dictionary with the configuration for the required fields
    '''
    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

    niskins_df = get_registered_niskins(DB, CRUISE_NUMBER).reset_index()

    # Loading fields
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
        subconfig='Niskin bottles',
        CRUISE_NUMBER=CRUISE_NUMBER
    )

    # Removing rows from dataframe where no missing values
    check_for_missing = list(output_config_dict['Data']['Required'].keys())
    check_for_missing = [c.lower() for c in check_for_missing]
    if 'pi_details' in check_for_missing:
        check_for_missing.remove('pi_details')
        check_for_missing = check_for_missing + ['pi_name', 'pi_email', 'pi_institution']
    if 'recordedby' in check_for_missing:
        check_for_missing.remove('recordedby')
        check_for_missing = check_for_missing + ['recordedby_name', 'recordedby_email', 'recordedby_institution']

    # If any required columns are missing, then 'all_required_present' = False
    niskins_df['all_required_present'] = ~niskins_df[check_for_missing].isna().any(axis = 1)

    # Keep all rows where all required_present is False AND
    # EITHER depths recorded is False OR elevations recorded is False
    niskins_df = niskins_df[(niskins_df['all_required_present'] == False)]

    # Sorting dataframe
    niskins_df.sort_values(by=['eventdate', 'eventtime', 'bottlenumber'], ascending=False, inplace=True)
    niskins_df = niskins_df.reset_index()

    return niskins_df, output_config_dict

@missingmetadata.route('/missingMetadata', methods=['GET'])
def missingmetadataredirect():
    '''
    Direct user to different pages
    With the current setup (26/06/2023) the user should not be able to input records
    with missing required metadata.
    The only records that could be missing records are activities pulled from the
    Toktlogger, or Niskin bottles pulled from the .btl files.
    Therefore, I am only searching for these.
    '''

    activities_df, output_config_dict = get_missing_activities()

    if len(activities_df) > 0:
        missing_activities = True
    else:
        missing_activities = False

    niskins_df, output_config_dict = get_missing_niskins()

    if len(niskins_df) > 0:
        missing_niskins = True
    else:
        missing_niskins = False

    return render_template(
    "missingMetadataRedirect.html",
    missing_activities = missing_activities,
    missing_niskins = missing_niskins
    )

@missingmetadata.route('/missingMetadata/Activities', methods=['GET', 'POST'])
def missing_metadata_activities():
    '''
    Page for logging missing metadata for sample activities (no parents - top of the pyramid)
    '''

    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())
    activities_df, output_config_dict = get_missing_activities()

    # Getting values
    num_rows = len(activities_df)
    geartypes = list(set(activities_df['geartype']))

    # Combining personnel details for use in single drop-down list
    activities_df['pi_details'] = activities_df.apply(lambda row : combine_personnel_details(row['pi_name'], row['pi_email']), axis=1)
    activities_df['recordedby'] = activities_df.apply(lambda row : combine_personnel_details(row['recordedby_name'], row['recordedby_email']), axis=1)

    required_fields_dic = output_config_dict['Data']['Required']
    if 'minimumDepthInMeters' in output_config_dict['Data']['Recommended'].keys() and 'maximumDepthInMeters' in output_config_dict['Data']['Recommended'].keys():
        required_fields_dic['minimumDepthInMeters'] = output_config_dict['Data']['Recommended']['minimumDepthInMeters']
        required_fields_dic['maximumDepthInMeters'] = output_config_dict['Data']['Recommended']['maximumDepthInMeters']
    if 'minimumElevationInMeters' in output_config_dict['Data']['Recommended'].keys() and 'maximumElevationInMeters' in output_config_dict['Data']['Recommended'].keys():
        required_fields_dic['minimumElevationInMeters'] = output_config_dict['Data']['Recommended']['minimumElevationInMeters']
        required_fields_dic['maximumElevationInMeters'] = output_config_dict['Data']['Recommended']['maximumElevationInMeters']

    if 'id' in output_config_dict['Data']['Required'].keys():
        pass
    elif 'id' in output_config_dict['Data']['Recommended'].keys():
        output_config_dict['Data']['Required']['id'] = output_config_dict['Data']['Recommended']['id']

    # Writing values to dictionary
    for key, val in required_fields_dic.items():
        activities_df.columns = activities_df.columns.str.replace(key.lower(), key)
        val['values'] = activities_df[key].values.tolist()

    if request.method == 'GET':
        return render_template(
        "missingMetadata.html",
        required_fields_dic=required_fields_dic,
        num_rows = num_rows,
        geartypes = geartypes,
        isnan=isnan
        )

    elif request.method == 'POST':
        form_input = request.form.to_dict(flat=False)
        df_personnel = get_personnel_df(DB=DB, table='personnel', CRUISE_NUMBER=CRUISE_NUMBER)

        required = list(required_fields_dic.keys())

        if 'pi_details' in required:
            required.remove('pi_details')
            required = required + ['pi_name', 'pi_email', 'pi_institution']
        if 'recordedBy' in required:
            required.remove('recordedBy')
            required = required + ['recordedBy_name', 'recordedBy_email', 'recordedBy_institution']

        df_to_submit = activities_df[required]
        fields_to_submit = []

        # if form_input['submit'] == ['bulk']:
        #     # Isolating df to selected gear type
        #     geartype = form_input['bulkgeartype']
        #     df_to_submit = df_to_submit.loc[df_to_submit['gearType'] == geartype[0]]
        #
        #     fields_to_submit.append('gearType')
        #
        #     for key, val in form_input.items():
        #         if key == 'bulkrecordedby':
        #             df_to_submit['recordedBy'] = ' | '.join(val)
        #             fields_to_submit.append('recordedBy')
        #         elif key == 'bulkpidetails':
        #             df_to_submit['pi_details'] = ' | '.join(val)
        #             fields_to_submit.append('pi_details')
        #
        # else:
        df_to_submit['pi_details'] = df_to_submit['recordedBy'] = None
        if form_input['submit'] == ['all']:
            rows = list(range(num_rows))
        else:
            rows = [int(r) for r in form_input['submit']]

        for key, value in form_input.items():
            if '|' in key and value != ['None']:
                field, row = key.split('|')
                fields_to_submit.append(field)
                row = int(row)
                if row in rows:
                    if len(value) == 1 and field not in ['pi_details', 'recordedBy']:
                        for term, vals in output_config_dict['Data']['Required'].items():
                            if term == field:
                                formatted_value = format_form_value(field, value, vals['format'])
                                df_to_submit[field][row] = formatted_value
                    elif field in ['pi_details','recordedBy']:
                        df_to_submit[field][row] = ' | '.join(format_form_value(field, value, 'text'))

        df_to_submit = df_to_submit.iloc[rows]

        df_to_submit.replace('None',None, inplace=True)
        fields_to_submit = list(set(fields_to_submit))

        df_to_submit[['pi_name','pi_email','pi_orcid','pi_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['pi_details'], df_personnel), axis = 1, result_type = 'expand')
        df_to_submit[['recordedBy_name','recordedBy_email','recordedBy_orcid','recordedBy_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['recordedBy'], df_personnel), axis = 1, result_type = 'expand')

        df_to_submit = df_to_submit.drop(columns=['pi_details','recordedBy'])
        for field in ['minimumDepthInMeters', 'maximumDepthInMeters', 'minimumElevationInMeters', 'maximumElevationInMeters']:
            required.remove(field)

        # Same check and submit steps regardless of which submit button pressed
        # after different preparations above

        good, errors = checker(
            data=df_to_submit,
            required=required,
            DB=DB,
            CRUISE_NUMBER=CRUISE_NUMBER,
            new=False,
            )

        if good == False:
            for error in errors:
                flash(error, category='error')

            return render_template(
            "missingMetadata.html",
            required_fields_dic=required_fields_dic,
            num_rows = num_rows,
            geartypes = geartypes,
            isnan=isnan
            )

        else:

            if 'parentid' in df_to_submit.columns:
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

            record_details = get_dict_for_list_of_fields(['modified','history'],FIELDS_FILEPATH)
            fields_to_submit_dict['columns']['modified'] = record_details['modified']
            fields_to_submit_dict['columns']['history'] = record_details['history']

            ids = list(df_to_submit['id'])

            fields_to_submit_dict['columns']['modified']['value'] = [dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") for n in range(len(df_to_submit))]
            fields_to_submit_dict['columns']['history']['value'] = list(activities_df.loc[activities_df['id'].isin(ids), 'history'])
            fields_to_submit_dict['columns']['history']['value'] = [n + '\n' + dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Updated using missingMetadata page for activities") for n in fields_to_submit_dict['columns']['history']['value']]

            update_record_metadata_catalogue(fields_to_submit_dict, DB=DB, CRUISE_NUMBER=CRUISE_NUMBER, IDs=ids)

            flash('Records updated successfully!', category='success')

            return redirect(url_for('missingmetadata.missing_metadata_activities'))

@missingmetadata.route('/missingMetadata/Niskin_bottles', methods=['GET', 'POST'])
def missing_metadata_niskins():
    '''
    Page for logging missing metadata for niskin bottles
    '''

    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())
    niskins_df, output_config_dict = get_missing_niskins()

    # Getting values
    num_rows = len(niskins_df)
    geartypes = list(set(niskins_df['geartype']))

    # Combining personnel details for use in single drop-down list
    niskins_df['pi_details'] = niskins_df.apply(lambda row : combine_personnel_details(row['pi_name'], row['pi_email']), axis=1)
    niskins_df['recordedby'] = niskins_df.apply(lambda row : combine_personnel_details(row['recordedby_name'], row['recordedby_email']), axis=1)

    required_fields_dic = output_config_dict['Data']['Required']

    if 'id' in output_config_dict['Data']['Required'].keys():
        pass
    elif 'id' in output_config_dict['Data']['Recommended'].keys():
        output_config_dict['Data']['Required']['id'] = output_config_dict['Data']['Recommended']['id']

    # Writing values to dictionary
    for key, val in required_fields_dic.items():
        niskins_df.columns = niskins_df.columns.str.replace(key.lower(), key)
        val['values'] = niskins_df[key].values.tolist()

    if request.method == 'GET':
        return render_template(
        "missingMetadata.html",
        required_fields_dic=required_fields_dic,
        num_rows = num_rows,
        geartypes = geartypes,
        isnan=isnan
        )

    elif request.method == 'POST':
        form_input = request.form.to_dict(flat=False)
        df_personnel = get_personnel_df(DB=DB, table='personnel', CRUISE_NUMBER=CRUISE_NUMBER)

        required = list(required_fields_dic.keys())

        if 'pi_details' in required:
            required.remove('pi_details')
            required = required + ['pi_name', 'pi_email', 'pi_institution']
        if 'recordedBy' in required:
            required.remove('recordedBy')
            required = required + ['recordedBy_name', 'recordedBy_email', 'recordedBy_institution']

        df_to_submit = niskins_df[required]
        fields_to_submit = []

        # if form_input['submit'] == ['bulk']:
        #     # Isolating df to selected gear type
        #     geartype = form_input['bulkgeartype']
        #     df_to_submit = df_to_submit.loc[df_to_submit['gearType'] == geartype[0]]
        #
        #     fields_to_submit.append('gearType')
        #
        #     for key, val in form_input.items():
        #         if key == 'bulkrecordedby':
        #             df_to_submit['recordedBy'] = ' | '.join(val)
        #             fields_to_submit.append('recordedBy')
        #         elif key == 'bulkpidetails':
        #             df_to_submit['pi_details'] = ' | '.join(val)
        #             fields_to_submit.append('pi_details')
        #
        # else:
        df_to_submit['pi_details'] = df_to_submit['recordedBy'] = None
        if form_input['submit'] == ['all']:
            rows = list(range(num_rows))
        else:
            rows = [int(r) for r in form_input['submit']]

        for key, value in form_input.items():
            if '|' in key and value != ['None']:
                field, row = key.split('|')
                fields_to_submit.append(field)
                row = int(row)
                if row in rows:
                    if len(value) == 1 and field not in ['pi_details', 'recordedBy']:
                        for term, vals in output_config_dict['Data']['Required'].items():
                            if term == field:
                                formatted_value = format_form_value(field, value, vals['format'])
                                df_to_submit[field][row] = formatted_value
                    elif field in ['pi_details','recordedBy']:
                        df_to_submit[field][row] = ' | '.join(format_form_value(field, value, 'text'))

        df_to_submit = df_to_submit.iloc[rows]

        df_to_submit.replace('None',None, inplace=True)
        fields_to_submit = list(set(fields_to_submit))

        df_to_submit[['pi_name','pi_email','pi_orcid','pi_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['pi_details'], df_personnel), axis = 1, result_type = 'expand')
        df_to_submit[['recordedBy_name','recordedBy_email','recordedBy_orcid','recordedBy_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['recordedBy'], df_personnel), axis = 1, result_type = 'expand')

        df_to_submit = df_to_submit.drop(columns=['pi_details','recordedBy'])

        # Same check and submit steps regardless of which submit button pressed
        # after different preparations above

        good, errors = checker(
            data=df_to_submit,
            required=required,
            DB=DB,
            CRUISE_NUMBER=CRUISE_NUMBER,
            new=False,
            )

        if good == False:
            for error in errors:
                flash(error, category='error')

            return render_template(
            "missingMetadata.html",
            required_fields_dic=required_fields_dic,
            num_rows = num_rows,
            geartypes = geartypes,
            isnan=isnan
            )

        else:

            if 'parentid' in df_to_submit.columns:
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

            record_details = get_dict_for_list_of_fields(['modified','history'],FIELDS_FILEPATH)
            fields_to_submit_dict['columns']['modified'] = record_details['modified']
            fields_to_submit_dict['columns']['history'] = record_details['history']

            ids = list(df_to_submit['id'])

            fields_to_submit_dict['columns']['modified']['value'] = [dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") for n in range(len(df_to_submit))]
            fields_to_submit_dict['columns']['history']['value'] = list(niskins_df.loc[niskins_df['id'].isin(ids), 'history'])
            fields_to_submit_dict['columns']['history']['value'] = [n + '\n' + dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Updated using missingMetadata page for niskin bottles") for n in fields_to_submit_dict['columns']['history']['value']]

            update_record_metadata_catalogue(fields_to_submit_dict, DB=DB, CRUISE_NUMBER=CRUISE_NUMBER, IDs=ids)

            flash('Records updated successfully!', category='success')

            return redirect(url_for('missingmetadata.missing_metadata_niskins'))
