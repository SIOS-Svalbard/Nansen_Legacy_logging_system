import yaml
import website.templategenerator.website.config.fields as fields
import os
from website.database.get_data import get_data, get_personnel_list
import pandas as pd

def get_fields(configuration, DB=None, CRUISE_NUMBER=None):
    '''
    Function to get the fields for a certain configuration in the 'template_configurations.yaml' file.

    Parameters
    ----------
    configuration: string
        The name of the configuration
    DB: dict
        Details of PSQL database
    CRUISE_NUMBER: string
        Cruise number, used in the name of some database tables
    '''
    setups = yaml.safe_load(open(os.path.join("website/configurations", "template_configurations.yaml"), encoding='utf-8'))['setups']

    for setup in setups:
        if setup['name'] == configuration:
            required_fields = setup['fields']['required']
            recommended_fields = setup['fields']['recommended']

    required_fields_dic = {}
    recommended_fields_dic = {}
    extra_fields_dic = {}

    groups = []
    extrafields=[]

    for field in fields.fields:
        if field['name'] in required_fields:
            required_fields_dic[field['name']] = {}
            required_fields_dic[field['name']]['disp_name'] = field['disp_name']
            required_fields_dic[field['name']]['description'] = field['description']
            required_fields_dic[field['name']]['format'] = field['format']
            if field['valid']['validate'] == 'list':
                table = field['valid']['source']
                if not DB:
                    df = pd.read_csv(f'website/templategenerator/website/config/{table}.csv')
                else:
                    try:
                        df = get_data(DB, table)
                    except:
                        df = get_data(DB, table+'_'+CRUISE_NUMBER)
                if field['name'] in ['pi_details', 'recordedBy_details']:
                    required_fields_dic[field['name']]['source'] = get_personnel_list(DB=DB, CRUISE_NUMBER=CRUISE_NUMBER, table='personnel')
                else:
                    required_fields_dic[field['name']]['source'] = list(df[field['name'].lower()])
        elif field['name'] in recommended_fields:
            recommended_fields_dic[field['name']] = {}
            recommended_fields_dic[field['name']]['disp_name'] = field['disp_name']
            recommended_fields_dic[field['name']]['description'] = field['description']
            recommended_fields_dic[field['name']]['format'] = field['format']
            if field['valid']['validate'] == 'list':
                table = field['valid']['source']
                if not DB:
                    df = pd.read_csv(f'website/templategenerator/website/config/{table}.csv')
                else:
                    try:
                        df = get_data(DB, table)
                    except:
                        df = get_data(DB, table+'_'+CRUISE_NUMBER)
                if field['name'] in ['pi_details', 'recordedBy_details']:
                    recommended_fields_dic[field['name']]['source'] = get_personnel_list(DB=DB, CRUISE_NUMBER=CRUISE_NUMBER, table='personnel')
                else:
                    recommended_fields_dic[field['name']]['source'] = list(df[field['name'].lower()])
        else:
            # Setting up extra fields for the 'modal' where the user can add more fields
            # Removing fields already included on the form and creating a list of groups so they can be grouped on the UI.
            if field['grouping'] not in ['Record Details', 'ID', 'Cruise Details'] and field['name'] not in ['pi_name', 'pi_email', 'pi_institution', 'recordedBy_name', 'recordedBy_email', 'recordedBy_institution']:
                extra_fields_dic[field['name']] = {}
                extra_fields_dic[field['name']]['disp_name'] = field['disp_name']
                extra_fields_dic[field['name']]['description'] = field['description']
                extra_fields_dic[field['name']]['format'] = field['format']
                extra_fields_dic[field['name']]['grouping'] = field['grouping']
                if field['valid']['validate'] == 'list':
                    table = field['valid']['source']
                    if not DB:
                        df = pd.read_csv(f'website/templategenerator/website/config/{table}.csv')
                    else:
                        try:
                            df = get_data(DB, table)
                        except:
                            df = get_data(DB, table+'_'+CRUISE_NUMBER)
                    if field['name'] in ['pi_details', 'recordedBy_details']:
                        extra_fields_dic[field['name']]['source'] = get_personnel_list(DB=DB, CRUISE_NUMBER=CRUISE_NUMBER, table='personnel')
                    else:
                        extra_fields_dic[field['name']]['source'] = list(df[field['name'].lower()])

                groups.append(field['grouping'])

    groups = sorted(list(set(groups)))

    personnel = get_personnel_list(DB=DB, CRUISE_NUMBER=CRUISE_NUMBER, table='personnel')

    return required_fields_dic, recommended_fields_dic, extra_fields_dic, groups
