from website import DB, TOKTLOGGER, FIELDS_FILEPATH
from website.lib.harvest_activities import harvest_activities
from website.lib.get_data import get_cruise, get_registered_niskins
from website.lib.get_setup_for_configuration import get_setup_for_configuration

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
