from flask import Blueprint, render_template, send_file, request
import uuid
import website.lib.create_pdf_of_data_matrices as uu

data_matrices_pdf = Blueprint('data_matrices_pdf', __name__)

@data_matrices_pdf.route('/data_matrices_pdf', methods=['GET', 'POST'])
def generate_data_matrices_pdf():

    numberPages = 1
    numberChildren = 24
    childName = ''
    parentName = ''

    if request.method == "GET":

        return render_template(
        "/data_matrices_pdf.html",
        numberPages = numberPages,
        numberChildren = numberChildren,
        childName = childName,
        parentName = parentName
        )

    elif request.method == "POST":

        form_input = request.form.to_dict(flat=False)

        numberPages = int(form_input['numberPages'][0])
        numberChildren = int(form_input['numberChildren'][0])
        childName = form_input['childName'][0]
        parentName = form_input['parentName'][0]

        filepath = '/tmp/data_matrices.pdf'

        uu.save_pages(filepath, gearText=parentName,sampleText=childName,M=numberChildren, N=numberPages)

        return send_file(filepath, as_attachment=True)
