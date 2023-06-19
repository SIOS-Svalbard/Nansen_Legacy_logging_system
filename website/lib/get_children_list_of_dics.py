from website.lib.get_data import get_children
from website.lib.expand_hstore import expand_hstore
from website.lib.other_functions import combine_personnel_details
from website.lib.get_setup_for_configuration import get_setup_for_configuration

def get_children_list_of_dics(DB, CRUISE_NUMBER, FIELDS_FILEPATH, ids):
    '''
    Create a list of dictionaries
    Each dictionary is a collection of fields and values to be plotted in a single table
    One table for each sample type (different fields based on configuration file)

    Parameters
    ----------
    DB: dict
        PSQL database details
    CRUISE_NUMBER: string
        Cruise number, used in PSQL table names
    FIELDS_FILEPATH: string
        Filepath to the fields
    ids: list
        List of UUIDS stored as strings to find and plot the children of

    Returns
    ---------
    children_samples_list_of_dics: list
        List of dictionaries (json)

    '''

    children_df = get_children(DB, CRUISE_NUMBER, ids)
    sampleTypes = list(set(children_df['sampletype']))
    children_samples_list_of_dics = []

    for sampleType in sampleTypes:

        try:
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
                subconfig=sampleType,
                CRUISE_NUMBER=CRUISE_NUMBER
            )
        except:
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
                subconfig='default',
                CRUISE_NUMBER=CRUISE_NUMBER
            )

        if 'id' in output_config_dict['Data']['Required'].keys():
            pass
        elif 'id' in output_config_dict['Data']['Recommended'].keys():
            output_config_dict['Data']['Required']['id'] = output_config_dict['Data']['Recommended']['id']
        elif 'id' in extra_fields_dic:
            output_config_dict['Data']['Required']['id'] = extra_fields_dic['id']
        if 'parentID' in output_config_dict['Data']['Required'].keys():
            output_config_dict['Data']['Required'].pop('parentID')

        sampleType_df = children_df.loc[children_df['sampletype'] == sampleType]

        sampleType_df['pi_details'] = sampleType_df.apply(lambda row : combine_personnel_details(row['pi_name'], row['pi_email']), axis=1)
        sampleType_df['recordedby'] = sampleType_df.apply(lambda row : combine_personnel_details(row['recordedby_name'], row['recordedby_email']), axis=1)

        sampleType_df = expand_hstore(sampleType_df)

        # Writing values to dictionary
        for key, val in output_config_dict['Data']['Required'].items():
            try:
                val['values'] = sampleType_df[key.lower()].values.tolist()
            except:
                val['values'] = sampleType_df[key].values.tolist()

        children_samples_list_of_dics.append(output_config_dict['Data']['Required'])

    return children_samples_list_of_dics
