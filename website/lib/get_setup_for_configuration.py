#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from website import DB, FIELDS_FILEPATH
from website.Learnings_from_AeN_template_generator.website.lib.get_configurations import get_config_fields
from website.lib.dropdown_lists_from_db import populate_dropdown_lists

def get_setup_for_configuration(fields_filepath,subconfig,CRUISE_NUMBER):

    config = 'Learnings from Nansen Legacy logging system'
    (
        output_config_dict,
        output_config_fields,
        extra_fields_dict,
        cf_standard_names,
        groups,
        dwc_terms
    ) = get_config_fields(
        fields_filepath=FIELDS_FILEPATH,
        config=config,
        subconfig=subconfig
    )

    for sheet in output_config_dict.keys():
        for key in output_config_dict[sheet].keys():
            if key not in ['Required CSV', 'Source']:
                fields_dict = output_config_dict[sheet][key]
                for field in fields_dict:
                    if fields_dict[field]['id'] == 'eventDate':
                        fields_dict[field]['format'] = 'date'
                        fields_dict[field]['valid']['validate'] = "date"
                        fields_dict[field]['valid']['criteria'] = "between"
                        fields_dict[field]['valid']['minimum'] = "2000-01-01"
                        fields_dict[field]['valid']['maximum'] = "=TODAY()+100"
                        fields_dict[field]['cell_format'] = {
                            "num_format": "yyyy-mm-dd"
                        }
                    elif fields_dict[field]['id'] == 'eventTime':
                        fields_dict[field]['format'] = 'time'
                        fields_dict[field]['valid']['validate'] = "time"
                        fields_dict[field]['valid']['criteria'] = "between"
                        fields_dict[field]['valid']['minimum'] = 0
                        fields_dict[field]['valid']['maximum'] = 0.9999999
                        fields_dict[field]['cell_format'] = {
                            "num_format": "hh:mm"
                        }
                output_config_dict[sheet][key] = populate_dropdown_lists(fields_dict, CRUISE_NUMBER)

    dwc_terms_tmp = []
    for term in dwc_terms:
        if term['id'] == 'eventDate':
            term['format'] = 'date'
            term['valid']['validate'] = "date"
            term['valid']['criteria'] = "between"
            term['valid']['minimum'] = "2000-01-01"
            term['valid']['maximum'] = "=TODAY()+100"
            term['cell_format'] = {
                "num_format": "yyyy-mm-dd"
            }
        elif term['id'] == 'eventTime':
            term['format'] = 'time'
            term['valid']['validate'] = "time"
            term['valid']['criteria'] = "between"
            term['valid']['minimum'] = 0
            term['valid']['maximum'] = 0.9999999
            term['cell_format'] = {
                "num_format": "hh:mm"
            }
        dwc_terms_tmp.append(term)
    dwc_terms = dwc_terms_tmp

    extra_fields_dict = populate_dropdown_lists(extra_fields_dict, CRUISE_NUMBER)
    dwc_terms = populate_dropdown_lists(dwc_terms, CRUISE_NUMBER)
    cf_standard_names = populate_dropdown_lists(cf_standard_names, CRUISE_NUMBER)

    # Creating a dictionary of all the fields.
    all_fields_dict = extra_fields_dict.copy()

    for sheet in output_config_dict.keys():
        for key in output_config_dict[sheet].keys():
            if key not in ['Required CSV', 'Source']:
                for field, values in output_config_dict[sheet][key].items():
                    all_fields_dict[field] = values

    added_fields_dic = {}
    added_cf_names_dic = {}
    added_dwc_terms_dic = {}
    dwc_terms_not_in_config = {} # Separate dictionary of dwc terms that doesn't include required or recommended terms in each sheet.

    for sheet in output_config_dict.keys():
        if output_config_dict[sheet]['Required CSV'] == True:
            added_cf_names_dic[sheet] = {}
            added_dwc_terms_dic[sheet] = {}
            added_fields_dic[sheet] = {}
            dwc_terms_tmp = dwc_terms
            for key in output_config_dict[sheet].keys():
                if key not in ['Required CSV', 'Source']:
                    fields_accounted_for = output_config_dict[sheet][key].keys()
                    idxs_to_remove = []
                    for idx, dwc_term in enumerate(dwc_terms_tmp):
                        if dwc_term['id'] in fields_accounted_for:
                            idxs_to_remove.append(idx)
                    dwc_terms_to_keep = [dwc_terms_tmp[i] for i in range(len(dwc_terms_tmp)) if i not in idxs_to_remove]
                    dwc_terms_tmp = dwc_terms_to_keep
            dwc_terms_not_in_config[sheet] = dwc_terms_tmp

    return (
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
    )
