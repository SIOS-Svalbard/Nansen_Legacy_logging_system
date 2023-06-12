from flask import Blueprint, render_template, request, flash, redirect, url_for
from website.lib.get_data import get_personnel_df, get_cruise
from website.lib.input_update_records import update_record_metadata_catalogue_df
from website.lib.harvest_activities import harvest_activities
from website.lib.checker import run as checker
from website.lib.other_functions import split_personnel_list, combine_personnel_details
from website import DB, TOKTLOGGER, FIELDS_FILEPATH
from datetime import datetime as dt
from math import isnan
from website.lib.get_setup_for_configuration import get_setup_for_configuration

missingmetadata = Blueprint('missingmetadata', __name__)

@missingmetadata.route('/missingMetadata', methods=['GET', 'POST'])
def missing_metadata():
    '''
    Generate template html page code
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
        subconfig='activity',
        CRUISE_NUMBER=CRUISE_NUMBER
    )
    # Removing rows from dataframe where no missing values
    check_for_missing = list(output_config_dict['Data']['Required'].keys())
    check_for_missing = [c.lower() for c in check_for_missing]
    if 'pi_details' in check_for_missing:
        check_for_missing.remove('pi_details')
        check_for_missing = check_for_missing + ['pi_name', 'pi_email', 'pi_orcid', 'pi_institution']
    if 'recordedby' in check_for_missing:
        check_for_missing.remove('recordedby')
        check_for_missing = check_for_missing + ['recordedby_name', 'recordedby_email', 'recordedby_orcid', 'recordedby_institution']

    activities_df['bool'] = activities_df[check_for_missing].isna().any(axis = 1)
    activities_df = activities_df.loc[activities_df['bool'] == True]

    # Sorting dataframe
    activities_df.sort_values(by=['eventdate', 'eventtime'], ascending=False, inplace=True)
    activities_df = activities_df.reset_index()

    # Getting values
    num_rows = len(activities_df)
    geartypes = list(set(activities_df['geartype']))

    # Combining personnel details for use in single drop-down list
    activities_df['pi_details'] = activities_df.apply(lambda row : combine_personnel_details(row['pi_name'], row['pi_email']), axis=1)
    activities_df['recordedby'] = activities_df.apply(lambda row : combine_personnel_details(row['recordedby_name'], row['recordedby_email']), axis=1)

    if 'id' in output_config_dict['Data']['Required'].keys():
        pass
    elif 'id' in output_config_dict['Data']['Recommended'].keys():
        output_config_dict['Data']['Required']['id'] = output_config_dict['Data']['Recommended']['id']

    # Writing values to dictionary
    for key, val in output_config_dict['Data']['Required'].items():
        activities_df.columns = activities_df.columns.str.replace(key.lower(), key)
        val['values'] = activities_df[key].values.tolist()

    for key, val in output_config_dict['Data']['Required'].items():
        print('\n******')
        print(key)
        print('***')
        print(val)

    if request.method == 'GET':
        return render_template(
        "missingMetadata.html",
        required_fields_dic=output_config_dict['Data']['Required'],
        num_rows = num_rows,
        geartypes = geartypes,
        isnan=isnan
        )

    elif request.method == 'POST':
        form_input = request.form.to_dict(flat=False)
        df_personnel = get_personnel_df(DB=DB, table='personnel', CRUISE_NUMBER=CRUISE_NUMBER)

        required = list(activity_fields_dic.keys())
        df_to_submit = activities_df[required]

        if 'pi_details' in required:
            required.remove('pi_details')
            required = required + ['pi_name', 'pi_email', 'pi_orcid', 'pi_institution']
        if 'recordedBy' in required:
            required.remove('recordedBy')
            required = required + ['recordedBy_name', 'recordedBy_email', 'recordedBy_orcid', 'recordedBy_institution']

        fields_to_submit = []

        if form_input['submit'] == ['bulk']:

            # Isolating df to selected gear type
            geartype = form_input['bulkgeartype']
            df_to_submit = df_to_submit.loc[df_to_submit['gearType'] == geartype[0]]

            fields_to_submit.append('gearType')

            for key, val in form_input.items():
                if key == 'bulkrecordedby':
                    df_to_submit['recordedBy'] = ' | '.join(val)
                    fields_to_submit.append('recordedBy')
                elif key == 'bulkpidetails':
                    df_to_submit['pi_details'] = ' | '.join(val)
                    fields_to_submit.append('pi_details')

        else:
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
                        if len(value) == 1 and key not in ['pi_details', 'recordedBy']:
                            df_to_submit[field][row] = value[0]
                        elif key in ['pi_details','recordedBy']:
                            df_to_submit[field][row] = ' | '.join(value)
                        elif len(value) == 0:
                            df_to_submit[field][row] = ''

            df_to_submit = df_to_submit.iloc[rows]

        # Same check and submit steps regardless of which submit button pressed
        # after different preparations above

        df_to_submit.replace('None','', inplace=True)
        fields_to_submit = list(set(fields_to_submit))

        if 'pi_details' in fields_to_submit:
            df_to_submit[['pi_name','pi_email','pi_orcid','pi_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['pi_details'], df_personnel), axis = 1, result_type = 'expand')
            fields_to_submit.remove('pi_details')
            fields_to_submit = fields_to_submit + ['pi_name', 'pi_email', 'pi_orcid', 'pi_institution']
        if 'recordedBy' in fields_to_submit:
            df_to_submit[['recordedBy_name','recordedBy_email','recordedBy_orcid','recordedBy_institution']] = df_to_submit.apply(lambda row : split_personnel_list(row['recordedBy'], df_personnel), axis = 1, result_type = 'expand')
            fields_to_submit.remove('recordedBy')
            fields_to_submit = fields_to_submit + ['recordedBy_name', 'recordedBy_email', 'recordedBy_orcid', 'recordedBy_institution']

        for col in df_to_submit.columns:
            if col not in fields_to_submit and col != 'id':
                df_to_submit.drop(col, axis=1, inplace=True)

        good, errors = checker(
            data=df_to_submit,
            required=fields_to_submit,
            DB=DB,
            CRUISE_NUMBER=CRUISE_NUMBER,
            new=False,
            )

        if good == False:
            for error in errors:
                flash(error, category='error')

            return render_template(
            "missingMetadata.html",
            activity_fields_dic=activity_fields_dic,
            num_rows = num_rows,
            geartypes = geartypes,
            personnel=personnel,
            isnan=isnan
            )

        else:
            for field in fields.fields:
                if field['name'] in fields_to_submit:
                    if field['format'] in ['int', 'double precision', 'time', 'date']:
                        df_to_submit[field['name']] = df_to_submit[field['name']].replace([''], 'NULL')
                        df_to_submit[field['name']].fillna('NULL', inplace=True)
                if field['format'] == 'time' and field['name'] in fields_to_submit:
                    df_to_submit[field['name']] = df_to_submit[field['name']].astype('object')
                    df_to_submit[field['name']].fillna('NULL', inplace=True)

            ids = list(activities_df['id'])
            df_to_submit['history'] = activities_df.loc[activities_df['id'].isin(ids), 'history'].iloc[0]
            df_to_submit['history'] = df_to_submit['history'] + '\n' + dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ Updated using missingMetadata page for activities")
            df_to_submit['modified'] = dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            update_record_metadata_catalogue_df(df_to_submit, metadata_df=False, DB=DB, CRUISE_NUMBER=CRUISE_NUMBER)

            flash('Records updated successfully!', category='success')

            return redirect(url_for('missingmetadata.missing_metadata'))
