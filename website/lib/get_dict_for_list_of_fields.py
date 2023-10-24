#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from website.Nansen_Legacy_template_generator.website.lib.pull_cf_standard_names import cf_standard_names_to_dic
from website.Nansen_Legacy_template_generator.website.lib.pull_other_fields import other_fields_to_dic
from website.Nansen_Legacy_template_generator.website.lib.pull_darwin_core_terms import dwc_terms_to_dic, dwc_extension_to_dic

def get_dict_for_list_of_fields(fields_list, FIELDS_FILEPATH):

    other_fields = other_fields_to_dic(FIELDS_FILEPATH)
    cf_standard_names = cf_standard_names_to_dic(FIELDS_FILEPATH)
    dwc_terms = dwc_terms_to_dic(FIELDS_FILEPATH)

    fields_dict = {}

    for field in other_fields:
        if field['id'] in fields_list:
            fields_dict[field['id']] = field

    for field in cf_standard_names:
        if field['id'] in fields_list:
            fields_dict[field['id']] = field

    for field in dwc_terms:
        if field['id'] in fields_list:
            fields_dict[field['id']] = field
            if field['id'] == 'eventDate':
                fields_dict[field['id']]['format'] = 'date'
                fields_dict[field['id']]['valid']['validate'] = "date"
                fields_dict[field['id']]['valid']['criteria'] = "between"
                fields_dict[field['id']]['valid']['minimum'] = "2000-01-01"
                fields_dict[field['id']]['valid']['maximum'] = "=TODAY()+100"
                fields_dict[field['id']]['cell_format'] = {
                    "num_format": "yyyy-mm-dd"
                }
            elif field['id'] == 'eventTime':
                fields_dict[field['id']]['format'] = 'time'
                fields_dict[field['id']]['valid']['validate'] = "time"
                fields_dict[field['id']]['valid']['criteria'] = "between"
                fields_dict[field['id']]['valid']['minimum'] = 0
                fields_dict[field['id']]['valid']['maximum'] = 0.9999999
                fields_dict[field['id']]['cell_format'] = {
                    "num_format": "hh:mm"
                }

    ordered_fields_dict = {}

    for field in fields_list:
        ordered_fields_dict[field] = fields_dict[field]

    return ordered_fields_dict
