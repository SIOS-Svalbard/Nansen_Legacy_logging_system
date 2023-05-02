#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from website.Learnings_from_AeN_template_generator.website.lib.pull_cf_standard_names import cf_standard_names_to_dic
from website.Learnings_from_AeN_template_generator.website.lib.pull_other_fields import other_fields_to_dic
from website.Learnings_from_AeN_template_generator.website.lib.pull_darwin_core_terms import dwc_terms_to_dic, dwc_extension_to_dic

def get_dict_for_list_of_fields(fields_list):

    other_fields = other_fields_to_dic()
    cf_standard_names = cf_standard_names_to_dic()
    dwc_terms = dwc_terms_to_dic()

    print(other_fields)

    fields_dict = {}
    return fields_dict
