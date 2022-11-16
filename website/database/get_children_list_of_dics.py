from website.database.get_data import get_children
from website.database.expand_hstore import expand_hstore
from website.configurations.get_configurations import get_fields
from website.other_functions.other_functions import combine_personnel_details

#def get_children_list_of_dics(DBNAME, METADATA_CATALOGUE, ids):
def get_children_list_of_dics(DB, METADATA_CATALOGUE, ids):
    '''
    Create a list of dictionaries
    Each dictionary is a collection of fields and values to be plotted in a single table
    One table for each sample type (different fields based on configuration file)

    Parameters
    ----------
    DBNAME: string
        Name of the PSQL database that contains the metadata catalogue
    METADATA_CATALOGUE: string
        Name of the table in the PSQL database
    ids: list
        List of UUIDS stored as strings to find and plot the children of

    Returns
    ---------
    children_samples_list_of_dics: list
        List of dictionaries (json)

    '''

    #children_df = get_children(DBNAME, METADATA_CATALOGUE, ids)
    children_df = get_children(DB, METADATA_CATALOGUE, ids)
    sampleTypes = list(set(children_df['sampletype']))
    children_samples_list_of_dics = []

    for sampleType in sampleTypes:

        try:
            #children_required_fields_dic, children_recommended_fields_dic, children_extra_fields_dic, children_groups = get_fields(configuration=sampleType, DBNAME=DBNAME)
            children_required_fields_dic, children_recommended_fields_dic, children_extra_fields_dic, children_groups = get_fields(configuration=sampleType, DB=DB)
        except:
            #children_required_fields_dic, children_recommended_fields_dic, children_extra_fields_dic, children_groups = get_fields(configuration='default', DBNAME=DBNAME)
            children_required_fields_dic, children_recommended_fields_dic, children_extra_fields_dic, children_groups = get_fields(configuration='default', DB=DB)
        if 'id' in children_required_fields_dic.keys():
            pass
        elif 'id' in children_recommended_fields_dic.keys():
            children_required_fields_dic['id'] = children_recommended_fields_dic['id']
        elif 'id' in extra_fields_dic:
            children_required_fields_dic['id'] = children_extra_fields_dic['id']
        if 'parentID' in children_required_fields_dic.keys():
            children_required_fields_dic.pop('parentID')

        sampleType_df = children_df.loc[children_df['sampletype'] == sampleType]

        sampleType_df['pi_details'] = sampleType_df.apply(lambda row : combine_personnel_details(row['pi_name'], row['pi_email']), axis=1)
        sampleType_df['recordedby_details'] = sampleType_df.apply(lambda row : combine_personnel_details(row['recordedby_name'], row['recordedby_email']), axis=1)

        sampleType_df = expand_hstore(sampleType_df)

        # Writing values to dictionary
        for key, val in children_required_fields_dic.items():
            try:
                val['values'] = sampleType_df[key.lower()].values.tolist()
            except:
                val['values'] = sampleType_df[key].values.tolist()

        children_samples_list_of_dics.append(children_required_fields_dic)

    return children_samples_list_of_dics
