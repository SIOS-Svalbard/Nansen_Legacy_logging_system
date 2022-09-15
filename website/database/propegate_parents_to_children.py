from website.database.get_data import get_metadata_for_list_of_ids
import website.database.fields as fields
import numpy as np

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

def propegate_parents_to_children(df_children,DBNAME, METADATA_CATALOGUE):

    parentIDs = list(df_children['parentID'])
    df_parents = get_metadata_for_list_of_ids(DBNAME, METADATA_CATALOGUE, parentIDs)

    inheritable = []  # For holding inheritable fields
    weak = []  # For holding weak inheritance
    for f in fields.fields:
        if f['name'].lower() in df_children.columns:
            df_children.columns = df_children.columns.str.replace(f['name'].lower(),f['name'])
        if f['name'].lower() in df_parents.columns:
            df_parents.columns = df_parents.columns.str.replace(f['name'].lower(),f['name'])
        if "inherit" in f and f["inherit"]:
            inheritable.append(f['name'])
            if "inherit_weak" in f and f["inherit_weak"]:
                weak.append(f['name'])

    for col in df_parents.columns:
        if col in inheritable:
            df_children['inherit'] = True
            if col in weak and col in df_children.columns:
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
