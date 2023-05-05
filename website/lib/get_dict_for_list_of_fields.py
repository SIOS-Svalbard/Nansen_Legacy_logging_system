#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from website.Learnings_from_AeN_template_generator.website.lib.pull_cf_standard_names import cf_standard_names_to_dic
from website.Learnings_from_AeN_template_generator.website.lib.pull_other_fields import other_fields_to_dic
from website.Learnings_from_AeN_template_generator.website.lib.pull_darwin_core_terms import dwc_terms_to_dic, dwc_extension_to_dic

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

    ordered_fields_dict = {}

    for field in fields_list:
        ordered_fields_dict[field] = fields_dict[field]

    return ordered_fields_dict
