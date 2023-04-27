from flask import Blueprint, render_template, request, send_file
from website.lib.get_data import get_cruise
from . import DB

generatetemplates = Blueprint('generatetemplates', __name__)

@generatetemplates.route('/generateTemplate', methods=['GET', 'POST'])
def generate_template():
    '''
    Generate template html page code
    '''

    cruise_details_df = get_cruise(DB)
    CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

    required_fields_dic, recommended_fields_dic, extra_fields_dic, groups = get_fields(configuration='activity', DB=DB, CRUISE_NUMBER=CRUISE_NUMBER)

    added_fields_dic = {}
    if request.method == 'POST':

        form_input = request.form.to_dict(flat=False)

        for key, val in form_input.items():
            if key not in required_fields_dic.keys() and key not in recommended_fields_dic.keys() and key != 'submitbutton':
                for field in fields.fields:
                    if field['name'] == key:
                        added_fields_dic[key] = {}
                        added_fields_dic[key]['disp_name'] = field['disp_name']
                        added_fields_dic[key]['description'] = field['description']

        if form_input['submitbutton'] == ['generateTemplate']:

            fields_list = list(required_fields_dic.keys())

            for field, val in form_input.items():
                if val == ['on']:
                    fields_list = fields_list + [field]

            filepath = '/tmp/generated_template.xlsx'

            write_file(filepath, fields_list, metadata=True, conversions=True, data=False, metadata_df=False, DB=DB, CRUISE_NUMBER=CRUISE_NUMBER)

            return send_file(filepath, as_attachment=True)

    if len(added_fields_dic) > 0:
        added_fields_bool = True
    else:
        added_fields_bool = False

    return render_template(
    "generateTemplate.html",
    required_fields_dic = required_fields_dic,
    recommended_fields_dic = recommended_fields_dic,
    extra_fields_dic = extra_fields_dic,
    groups = groups,
    added_fields_dic = added_fields_dic,
    added_fields_bool = added_fields_bool
    )
