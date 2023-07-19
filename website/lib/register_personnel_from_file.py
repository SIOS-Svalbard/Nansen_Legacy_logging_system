import pandas as pd
from website import DB
from website.lib.get_data import get_data, get_cruise
import psycopg2
import uuid

cruise_details_df = get_cruise(DB)
CRUISE_NUMBER = str(cruise_details_df['cruise_number'].item())

def check_content(df, header_row):

    missing_first_names = []
    missing_last_names = []
    missing_emails = []
    invalid_emails = []
    already_registered_personnel = []
    missing_institutions = []
    invalid_institutions = []
    invalid_new_institutions = []
    new_institution_already_registered = []
    invalid_orcids = []
    institutionsToRegister = []

    registered_personnel_df = get_data(DB, 'personnel_'+str(CRUISE_NUMBER))
    registered_emails = list(registered_personnel_df['email'])
    registered_institutions = list(registered_personnel_df['email'])

    institutions_df = get_data(DB, 'institutions')
    registered_institutions = list(institutions_df['full_name'])

    for idx, row in df.iterrows():

        row_num = idx + header_row + 2

        firstName = row['firstName']
        lastName = row['lastName']
        email = row['email']
        orcID = row['orcID']
        institution = row['institution']
        institutionToRegister = row['institutionToRegister']

        # Validations for first name
        if type(firstName) != str:
            missing_first_names.append(row_num)

        # Validations for last name
        if type(lastName) != str:
            missing_last_names.append(row_num)

        # Validations for email
        if type(email) != str:
            missing_emails.append(row_num)
        elif '@' not in email:
            invalid_emails.append(row_num)
        elif email in registered_emails:
            already_registered_personnel.append(row_num)

        # Validations for OrcID
        if type(orcID) == str:
            if len(orcID) != 37:
                invalid_orcids.append(row_num)
            elif orcID.startswith('https://orcid.org/') == False:
                invalid_orcids.append(row_num)
        else:
            df['orcID'][idx] = 'NULL'

        # Validations for institution
        if type(institution) != str or institution == 'Other':
            if type(institutionToRegister) != str:
                missing_institutions.append(row_num)
            elif institutionToRegister in registered_institutions:
                new_institution_already_registered.append(row_num)
            elif len(institutionToRegister) < 7:
                invalid_new_institutions.append(row_num)
            else:
                institutionsToRegister.append(institutionToRegister)
                df['institution'][idx] = institutionToRegister

        elif institution not in registered_institutions:
            invalid_institutions.append(row_num)

    duplicates = df[df.duplicated('email', keep=False)]
    duplicate_groups = duplicates.groupby('email').groups
    duplicate_emails = [duplicates.loc[group].index.tolist() for group in duplicate_groups.values()]

    content_errors = []

    if len(missing_first_names) > 0:
        content_errors.append(
            f'Missing first name for row(s): {missing_first_names}'
        )
    if len(missing_last_names) > 0:
        content_errors.append(
            f'Missing last name for row(s): {missing_last_names}'
        )
    if len(missing_emails) > 0:
        content_errors.append(
            f'Missing email for row(s): {missing_emails}'
        )
    if len(invalid_emails) > 0:
        content_errors.append(
            f'Email must include an @ symbol, row(s): {invalid_emails}'
        )
    if len(already_registered_personnel) > 0:
        content_errors.append(
            f'Person with same email already registered, row(s): {already_registered_personnel}'
        )
    if len(invalid_orcids) > 0:
        content_errors.append(
            f'OrcID should be 37 characers long and begin with https://orcid.org/, row(s): {invalid_orcids}'
        )
    if len(missing_institutions) > 0:
        content_errors.append(
            f'Missing institution, row(s): {missing_institutions}'
        )
    if len(invalid_institutions) > 0:
        content_errors.append(
            f'Institution not registered and should not be listed in institution column, row(s): {invalid_institutions}'
        )
    if len(new_institution_already_registered) > 0:
        content_errors.append(
            f'Institution already registered, please select it in the institution column, row(s): {new_institution_already_registered}'
        )
    if len(invalid_new_institutions) > 0:
        content_errors.append(
            f'Institution to register should be at least 7 characters long. Please use the full name. Row(s): {invalid_new_institutions}'
        )
    if len(duplicate_emails) > 0:
        content_errors.append(
            f'Same email address listed more than once in the file. Row(s): {duplicate_emails}'
        )

    institutionsToRegister = list(set(institutionsToRegister))

    return content_errors, institutionsToRegister, df

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

        header_row = 5 # Hidden row on row 10

        if filepath.endswith(".xlsx"):
            try:
                df = pd.read_excel(filepath, sheet_name = 'Personnel', header=header_row)
            except:
                errors.append("Data couldn't be read from the Personnel sheet. Did you upload the correct file? The column headers should be on hidden row 6.")
                good = False
                return good, errors

            content_errors, institutionsToRegister, df = check_content(df, header_row)

            errors = errors + content_errors
            if len(errors) > 0:
                good = False
                return good, errors

            else:
                conn = psycopg2.connect(**DB)
                cur = conn.cursor()
                for institution in institutionsToRegister:
                    cur.execute(f"INSERT INTO institutions (id, full_name, created) VALUES ('{uuid.uuid4()}', '{institution}', CURRENT_TIMESTAMP);")

                for idx, row in df.iterrows():
                    first_name = row['firstName']
                    last_name = row['lastName']
                    email = row['email']
                    personnel = f"{first_name} {last_name} ({email})"
                    orcid = row['orcID']
                    institution = row['institution']
                    if type(orcid) == str and orcid != 'NULL':
                        cur.execute(f"INSERT INTO personnel_{CRUISE_NUMBER} (id, personnel, first_name, last_name, institution, email, orcid, created) VALUES ('{uuid.uuid4()}', '{personnel}', '{first_name}','{last_name}','{institution}','{email}','{orcid}', CURRENT_TIMESTAMP);")
                    else:
                        cur.execute(f"INSERT INTO personnel_{CRUISE_NUMBER} (id, personnel, first_name, last_name, institution, email, created) VALUES ('{uuid.uuid4()}', '{personnel}', '{first_name}','{last_name}','{institution}','{email}', CURRENT_TIMESTAMP);")
                conn.commit()
                cur.close()
                conn.close()

        else:
            errors.append('File must be an "XLSX" file.')
            good = False

    return good, errors
