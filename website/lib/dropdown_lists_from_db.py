import pandas as pd
from website import DB, CRUISE_NUMBER
from website.lib.get_data import get_stations_list, get_personnel_list

def get_dropdown_list_from_db(field):
    if field == 'stationName':
        stations = get_stations_list(DB=DB, CRUISE_NUMBER=CRUISE_NUMBER)
        return stations
    elif field in ['recordedBy_details', 'pi_details']:
        personnel = get_personnel_list(DB=DB, CRUISE_NUMBER=CRUISE_NUMBER)
        return personnel
    else:
        df = get_data(DB, field)
        return list(df[field])

def populate_dropdown_lists(fields_dict):

    fields_with_dropdown_list = [
        'kingdom',
        'sex',
        'sampleType',
        'gearType',
        'intendedMethod',
        'storageTemp',
        'filter',
        'recordedBy_details',
        'pi_details',
        'stationName',
    ]

    if isinstance(fields_dict, list):
        fields_with_dropdowns = []
        for field in fields_dict:
            if field['id'] in fields_with_dropdown_list:
                field['valid']['validate'] = 'list'
                field['valid']['source'] = get_dropdown_list_from_db(field['id'])
                field['valid']['error_message'] = 'Not a valid value, pick a value from the drop-down list.'
            fields_with_dropdowns.append(field)
        return fields_with_dropdowns

    else:
        for field in fields_dict.keys():
            if field in fields_with_dropdown_list:
                fields_dict[field]['valid']['validate'] = 'list'
                fields_dict[field]['valid']['source'] = get_dropdown_list_from_db(field)
                fields_dict[field]['valid']['error_message'] = 'Not a valid value, pick a value from the drop-down list.'
        return fields_dict
