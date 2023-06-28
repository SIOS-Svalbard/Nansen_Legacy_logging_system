
def register_personnel_from_file(f):

    good = True
    errors = []

    if f.filename == '':
        good = False
        errors.append('No file selected')
        return good, errors

    else:

        filepath = '/tmp/'+f.filename
        f.save(filepath)

    return good, errors
