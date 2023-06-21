from website.lib.get_data import get_metadata_for_list_of_ids
import psycopg2
import pandas as pd
from website import CONFIG

def copy_from_parent(parentID, col, df_parents, child_value=None, inherit=False):
    if inherit == True:
        parent_value = df_parents.loc[df_parents['id'] == parentID, col].item()
        return parent_value
    else:
        return child_value

def check_whether_to_inherit(parentID, col, df_parents, child_value=None, weak=True):
    '''
    1. If no parent value, don't inherit
    2. If parent value but no child value, inherit
    3. If parent value and child value, don't inherit if 'weak', inherit if not 'weak'
    '''
    parent_value = df_parents.loc[df_parents['id'] == parentID, col].item()

    if parent_value in [None, '', 'NULL']:
        return False
    else:
        if child_value in [None, '', 'NULL']:
            return True
        else:
            if weak == True:
                return False
            else:
                return True

def propegate_parents_to_children(df_children,DB, CRUISE_NUMBER):

    try:
        parentIDs = list(df_children['parentID'])
    except:
        try:
            parentIDs = list(df_children['parentid'])
        except:
            return df_children
    df_parents = get_metadata_for_list_of_ids(DB, CRUISE_NUMBER, parentIDs)

    # Check if every row in each column contains None
    all_none_columns = [col for col in df_parents.columns if df_parents[col].isna().all()]

    # Remove the columns with all None values
    df_parents = df_parents.drop(columns=all_none_columns)

    inheritable = CONFIG["metadata_catalogue"]["fields_to_inherit"]
    weak = CONFIG["metadata_catalogue"]["fields_to_inherit_if_not_logged_for_children"]

    inheritable_lower = [ii.lower() for ii in inheritable]
    weak_lower = [ii.lower() for ii in weak]
    df_children_columns = list(df_children.columns)
    df_children_columns_lower = [ii.lower() for ii in df_children_columns]
    df_parents_columns = list(df_parents.columns)
    df_parents_columns_lower = [ii.lower() for ii in df_parents_columns]

    for col in df_children.columns:
        if col in df_parents_columns:
            pass
        elif col.lower() in df_parents_columns_lower:
            df_parents.rename(columns = {col.lower(): col}, inplace = True)

    for col in df_parents.columns:
        if col in inheritable + weak + inheritable_lower + weak_lower:
            df_children['inherit'] = True
            if col in weak or col in weak_lower and col in df_children_columns or col in df_children_columns_lower:
                df_children['inherit'] = df_children.apply(lambda row : check_whether_to_inherit(row['parentID'], col, df_parents, child_value = row[col], weak=True), axis=1)
                df_children[col] = df_children.apply(lambda row : copy_from_parent(row['parentID'], col, df_parents, child_value = row[col], inherit = row['inherit']), axis=1)
            else:
                if col in df_children.columns:
                    df_children['inherit'] = df_children.apply(lambda row : check_whether_to_inherit(row['parentID'], col, df_parents, child_value = row[col], weak=False), axis=1)
                    df_children[col] = df_children.apply(lambda row : copy_from_parent(row['parentID'], col, df_parents, child_value = row[col], inherit = row['inherit']), axis=1)
                else:
                    df_children['inherit'] = df_children.apply(lambda row : check_whether_to_inherit(row['parentID'], col, df_parents, weak=False), axis=1)
                    df_children[col] = df_children.apply(lambda row : copy_from_parent(row['parentID'], col, df_parents, inherit = row['inherit']), axis=1)
            df_children.drop('inherit', axis=1, inplace=True)

    return df_children

def find_all_children(IDs,DB, CRUISE_NUMBER):
    '''
    Return a list of child IDs for parent IDs provided.
    Children, grandchildren etc are all included in the returned list
    This is useful for when samples are updated. In this case, the children must also be updated
    for fields that should be inherited

    Parameters
    ----------
    IDs : list
        List of IDs whose children you want to find
    DB: str
        Name of PSQL database that hosts the metadata catalogue
        and other tables where lists of values for certain fields are registered
    CRUISE_NUMBER: str
        Cruise number, used in some PSQL table names

    Returns
    -------
    children_IDs : list
        List of IDs for all the children, grandchildren etc.

    '''

    conn = psycopg2.connect(**DB)

    moreChildren = True
    children_IDs = []

    while moreChildren == True:
        if len(IDs) == 1:
            df = pd.read_sql(f"SELECT id FROM metadata_catalogue_{CRUISE_NUMBER} where parentid = '{IDs[0]}';", con=conn)
        else:
            df = pd.read_sql(f'SELECT id FROM metadata_catalogue_{CRUISE_NUMBER} where parentid in {tuple(IDs)};', con=conn)
        newChildren = df['id'].to_list()
        newChildren = [p for p in newChildren if p not in IDs]
        [children_IDs.append(p) for p in newChildren if type(p) == str]
        IDs = newChildren
        if len(newChildren) == 0:
            moreChildren = False

    return children_IDs
