from flask import Blueprint, render_template, send_file, request
import uuid

uuid_generator = Blueprint('uuid_generator', __name__)

@uuid_generator.route('/uuid_generator', methods=['GET', 'POST'])
def generate_uuids():

    uuids = [str(uuid.uuid4()) for _ in range(4)]
    numberUUIDs = 100 # Number of UUIDs to write to a file by default

    if request.method == "GET":

        return render_template(
        "/uuid_generator.html",
        uuids = uuids,
        numberUUIDs = numberUUIDs
        )

    elif request.method == "POST":
        form_input = request.form.to_dict(flat=False)
        numberUUIDs = int(form_input["numberUUIDs"][0])

        if "generateMore" in form_input:

            uuids = [str(uuid.uuid4()) for _ in range(4)]

            return render_template(
            "/uuid_generator.html",
            uuids = uuids,
            numberUUIDs = numberUUIDs
            )

        elif "uuidsFile" in form_input:

            filepath = f'/tmp/uuids.txt'
            with open(filepath, 'w') as f:
                for _ in range(numberUUIDs):
                    f.write(str(uuid.uuid4()) + '\n')

            return send_file(filepath, as_attachment=True)
