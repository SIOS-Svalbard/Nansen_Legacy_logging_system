from flask import Blueprint, render_template, request, flash, redirect, send_file
from website.lib.get_data import get_cruise
from website import DB, FIELDS_FILEPATH
from website.Nansen_Legacy_template_generator.website.lib.create_template import create_template
from website.lib.get_setup_for_configuration import get_setup_for_configuration
from website.lib.other_functions import combine_fields_dictionaries

chooseactivityfields = Blueprint('chooseactivityfields', __name__)

@chooseactivityfields.route('/generateActivityTemplate', methods=['GET', 'POST'])
def choose_activity_fields():
    '''
    Generate template html page code
    '''
    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

    config = 'Nansen Legacy logging system'
    subconfig = 'Activities'

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
        subconfig=subconfig,
        CRUISE_NUMBER=CRUISE_NUMBER
    )

    if request.method == 'POST':

        form_input = request.form.to_dict(flat=False)
        all_form_keys = request.form.keys()

        # 1. Preserve the values added in the form for each field by adding them to the relevant dictionaries
        for sheet in output_config_dict.keys():
            for requirement in output_config_dict[sheet].keys():
                if requirement not in ['Required CSV', 'Source']:
                    for field, vals in output_config_dict[sheet][requirement].items():
                        if field in form_input:
                            vals['checked'] = form_input[field]
                        else:
                            vals['checked'] = ['']

        # 2. Adding extra fields selected by user

        # CF standard names
        for field in cf_standard_names:
            for sheet in added_cf_names_dic.keys():
                if sheet not in ['Required CSV', 'Source']:
                    for form_key in all_form_keys:
                        if form_key == field['id']:
                            added_cf_names_dic[sheet][field['id']] = {}
                            added_cf_names_dic[sheet][field['id']]['id'] = field['id']
                            added_cf_names_dic[sheet][field['id']]['disp_name'] = field['id']
                            added_cf_names_dic[sheet][field['id']]['valid'] = field['valid']
                            if field["description"] == None:
                                field["description"] = ""
                            added_cf_names_dic[sheet][field['id']]['description'] = f"{field['description']} \ncanonical units: {field['canonical_units']}"
                            added_cf_names_dic[sheet][field['id']]['format'] = field['format']
                            added_cf_names_dic[sheet][field['id']]['grouping'] = field['grouping']
                            if field['id'] in form_input:
                                added_cf_names_dic[sheet][field['id']]['checked'] = form_input[field['id']]
                            else:
                                added_cf_names_dic[sheet][field['id']]['checked'] = ['']

        # Darwin Core terms
        for sheet in dwc_terms_not_in_config.keys():
            for term in dwc_terms_not_in_config[sheet]:
                for form_key in all_form_keys:
                    if form_key == term['id']:
                        added_dwc_terms_dic[sheet][term['id']] = {}
                        added_dwc_terms_dic[sheet][term['id']]['id'] = term['id']
                        added_dwc_terms_dic[sheet][term['id']]['disp_name'] = term['id']
                        added_dwc_terms_dic[sheet][term['id']]['valid'] = term['valid']
                        if term["description"] == None:
                            term["description"] = ""
                        added_dwc_terms_dic[sheet][term['id']]['description'] = term['description']
                        added_dwc_terms_dic[sheet][term['id']]['format'] = term["format"]
                        added_dwc_terms_dic[sheet][term['id']]['grouping'] = term["grouping"]
                        if term['id'] in form_input:
                            added_dwc_terms_dic[sheet][term['id']]['checked'] = form_input[term['id']]
                        else:
                            added_dwc_terms_dic[sheet][term['id']]['checked'] = ['']

        # Other fields (not CF standard names or DwC terms - terms designed for the template generator and logging system)
        for field, vals in extra_fields_dict.items():
            for form_key in all_form_keys:
                if field == form_key:
                    added_fields_dic['Data'][field] = vals
                    if field in form_input:
                        added_fields_dic[sheet][field]['checked'] = form_input[field]
                    else:
                        added_fields_dic[sheet][field]['checked'] = ['']


        if form_input['submitbutton'] == ['addfields']:
            pass

        elif form_input['submitbutton'] == ['generateTemplate']:

            filepath = f'/tmp/{CRUISE_NUMBER}_activities.xlsx'

            template_fields_dict = combine_fields_dictionaries(
                output_config_dict,
                added_fields_dic,
                added_cf_names_dic,
                added_dwc_terms_dic
            )

            create_template(
                filepath = filepath,
                template_fields_dict = template_fields_dict,
                fields_filepath = FIELDS_FILEPATH,
                config = config,
                subconfig=subconfig,
                metadata=False,
                conversions=True,
                split_personnel_columns=True
            )

            return send_file(filepath, as_attachment=True)

    return render_template(
    "chooseActivityFields.html",
    output_config_dict=output_config_dict,
    extra_fields_dict = extra_fields_dict,
    groups = groups,
    cf_standard_names=cf_standard_names,
    dwc_terms_not_in_config=dwc_terms_not_in_config,
    added_fields_dic=added_fields_dic,
    added_cf_names_dic=added_cf_names_dic,
    added_dwc_terms_dic=added_dwc_terms_dic,
    )
