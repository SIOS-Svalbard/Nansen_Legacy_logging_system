import psycopg2
import psycopg2.extras
import getpass
import pandas as pd
import website.database.fields as fields
import website.database.metadata_fields as metadata_fields

def insert_into_metadata_catalogue(form_input, DB, CRUISE_NUMBER):

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    string_1 = f'INSERT INTO metadata_catalogue_{CRUISE_NUMBER} ('
    string_2 = ''
    string_3 = ') VALUES ('
    string_4 = ''
    string_5 = ');'

    # MAIN FIELDS
    for field in fields.fields:
        if field['name'] in form_input.keys() and field['hstore'] == False:
            string_2 = string_2 + field['name'] +", "
            if field['format'] in ['text', 'uuid', 'date', 'time', 'timestamp with time zone'] and form_input[field['name']] != 'NULL':
                string_4 = string_4 + "'" + form_input[field['name']] + "'" + ", "
            else:
                string_4 = string_4 + form_input[field['name']] + ", "

    string_2 = string_2[:-2]
    string_4 = string_4[:-2]

    # HSTORE FIELDS
    n = 0
    for field in fields.fields:
        if field['name'] in form_input.keys() and field['hstore'] != False and form_input[field['name']] != '':
            if n == 0:
                string_2 = string_2 + ", other"
                string_4 = string_4 + ", '"
                n = n + 1
            string_4 = string_4 + f'''"{field['name']}" => "{form_input[field['name']]}", '''

    if n != 0:
        string_4 = string_4[:-2] + "'"

    exe_str = string_1 + string_2 + string_3 + string_4 + string_5

    cur.execute(exe_str)

    conn.commit()
    cur.close()
    conn.close()

def update_record_metadata_catalogue(form_input, DB, CRUISE_NUMBER, ID):

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    string_1 = f'UPDATE metadata_catalogue_{CRUISE_NUMBER} SET '
    string_2 = ''
    string_3 = ''
    string_4 = ''
    string_5 = f" WHERE id = '{ID}';"

    # MAIN FIELDS
    for field in fields.fields:
        if field['name'] in form_input.keys() and field['hstore'] == False:
            if field['format'] in ['text', 'uuid', 'date', 'time', 'timestamp with time zone'] and form_input[field['name']] != 'NULL':
                string_2 = string_2 + field['name'] + ' = ' + "'" + form_input[field['name']] + "'" + ', '
            else:
                string_2 = string_2 + field['name'] + ' = ' + form_input[field['name']] + ', '

    string_2 = string_2[:-2]

    # HSTORE FIELDS
    n = 0
    for field in fields.fields:
        if field['name'] in form_input.keys() and field['hstore'] == 'other':
            if n == 0:
                string_3 = string_3 + ", other = other || hstore(array["
                string_4 = string_4 + "], array ["
                n = n + 1
            string_3 = string_3 + f"'{field['name']}', "

            string_4 = string_4 + f"'{form_input[field['name']]}', "

    if n != 0:
        string_3 = string_3[:-2]
        string_4 = string_4[:-2] + "])"

    exe_str = string_1 + string_2 + string_3 + string_4 + string_5

    cur.execute(exe_str)

    # Removing hstore fields when value deleted when updating the record
    for field in fields.fields:
        if field['name'] in form_input.keys() and field['hstore'] == 'other':
            if form_input[field['name']] == '' or form_input[field['name']] == 'NULL':
                exe_str = f"UPDATE {METADATA_CATALOGUE} SET other = delete(other, '{field['name']}')"
                cur.execute(exe_str)

    conn.commit()
    cur.close()
    conn.close()

def insert_into_metadata_catalogue_df(data_df, metadata_df, DB, CRUISE_NUMBER):

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    for idx, row in data_df.iterrows():

        string_1 = f'INSERT INTO metadata_catalogue_{CRUISE_NUMBER} ('
        string_2 = ''
        string_3 = ') VALUES ('
        string_4 = ''
        string_5 = ');'

        # MAIN FIELDS
        for field in fields.fields:
            if field['name'] in data_df.columns and field['hstore'] == False:
                string_2 = string_2 + field['name'] +", "
                if field['format'] in ['text', 'uuid', 'date', 'time', 'timestamp with time zone'] and row[field['name']] != 'NULL':
                    string_4 = string_4 + "'" + str(row[field['name']]) + "'" + ", "
                else:
                    string_4 = string_4 + str(row[field['name']]) + ", "

        string_2 = string_2[:-2]
        string_4 = string_4[:-2]

        # HSTORE FIELDS
        n = 0
        for field in fields.fields:
            if field['name'] in data_df.columns and field['hstore'] != False and row[field['name']] != '':
                if n == 0:
                    string_2 = string_2 + ", other"
                    string_4 = string_4 + ", '"
                    n = n + 1
                string_4 = string_4 + f'''"{field['name']}" => "{row[field['name']]}", '''

        if n != 0:
            string_4 = string_4[:-2] + "'"

        if isinstance(metadata_df, pd.DataFrame):
            # METADATA INTO METADATA HSTORE
            n = 0
            for metadata_field in metadata_fields.metadata_fields:
                if metadata_field['name'] in metadata_df.columns and metadata_df[metadata_field['name']].item() != 'NULL':
                    if n == 0:
                        string_2 = string_2 + ", metadata"
                        string_4 = string_4 + ", '"
                        n = n + 1
                    string_4 = string_4 + f'''"{metadata_field['name']}" => "{metadata_df[metadata_field['name']].item()}", '''

            if n != 0:
                string_4 = string_4[:-2] + "'"

        exe_str = string_1 + string_2 + string_3 + string_4 + string_5

        cur.execute(exe_str)

    conn.commit()
    cur.close()
    conn.close()

def update_record_metadata_catalogue_df(data_df, metadata_df, DB, CRUISE_NUMBER):

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    for idx, row in data_df.iterrows():
        string_1 = f'UPDATE metadata_catalogue_{CRUISE_NUMBER} SET '
        string_2 = ''
        string_3 = ''
        string_4 = ''
        string_5 = ''
        string_6 = ''
        string_7 = f" WHERE id = '{row['id']}';"

        # MAIN FIELDS
        for field in fields.fields:
            if field['name'] in data_df.columns and field['hstore'] == False:
                if field['format'] in ['text', 'uuid', 'date', 'time', 'timestamp with time zone'] and str(row[field['name']]) != 'NULL':
                    string_2 = string_2 + field['name'] + ' = ' + "'" + str(row[field['name']]) + "'" + ', '
                else:
                    string_2 = string_2 + field['name'] + ' = ' + str(row[field['name']]) + ', '

        string_2 = string_2[:-2]

        # HSTORE FIELDS
        n = 0
        for field in fields.fields:
            if field['name'] in data_df.columns and field['hstore'] == 'other':
                if n == 0:
                    string_3 = string_3 + ", other = other || hstore(array["
                    string_4 = string_4 + "], array ["
                    n = n + 1
                string_3 = string_3 + f"'{field['name']}', "

                string_4 = string_4 + f"'{str(row[field['name']])}', "

        if n != 0:
            string_3 = string_3[:-2]
            string_4 = string_4[:-2] + "])"

        # METADATA HSTORE FIELDS
        if isinstance(metadata_df, pd.DataFrame):
            n = 0
            for metadata_field in metadata_fields.metadata_fields:
                if metadata_field['name'] in metadata_df.columns and metadata_df[metadata_field['name']].item() != 'NULL':
                    if n == 0:
                        string_5 = string_5 + ", metadata = metadata || hstore(array["
                        string_6 = string_6 + "], array ["
                        n = n + 1
                    string_5 = string_5 + f"'{metadata_field['name']}', "

                    string_6 = string_6 + f"'{str(metadata_df[metadata_field['name']].item())}', "

            if n != 0:
                string_5 = string_5[:-2]
                string_6 = string_6[:-2] + "])"

        exe_str = string_1 + string_2 + string_3 + string_4 + string_5 + string_6 + string_7
        print(exe_str)
        cur.execute(exe_str)

        # Removing hstore fields when value deleted when updating the record
        for field in fields.fields:
            if field['name'] in data_df.columns and field['hstore'] == 'other':
                if str(row[field['name']]) == '' or str(row[field['name']]) == 'NULL':
                    exe_str = f"UPDATE {METADATA_CATALOGUE} SET other = delete(other, '{field['name']}')"
                    cur.execute(exe_str)

    conn.commit()
    cur.close()
    conn.close()
