import psycopg2
import psycopg2.extras
import getpass
import pandas as pd
import website.database.fields as fields

def insert_into_metadata_catalogue(form_input, DBNAME, METADATA_CATALOGUE):

    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    cur = conn.cursor()

    string_1 = f'INSERT INTO {METADATA_CATALOGUE} ('
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

def update_record_metadata_catalogue(form_input, DBNAME, METADATA_CATALOGUE):

    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    cur = conn.cursor()

    string_1 = f'UPDATE {METADATA_CATALOGUE} SET '
    string_2 = ''
    string_3 = ''
    string_4 = ''
    string_5 = f" WHERE id = '{form_input['id']}';"

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

def insert_into_metadata_catalogue_df(df, DBNAME, METADATA_CATALOGUE):

    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    cur = conn.cursor()

    for idx, row in df.iterrows():

        string_1 = f'INSERT INTO {METADATA_CATALOGUE} ('
        string_2 = ''
        string_3 = ') VALUES ('
        string_4 = ''
        string_5 = ');'

        # MAIN FIELDS
        for field in fields.fields:
            if field['name'] in df.columns and field['hstore'] == False:
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
            if field['name'] in df.columns and field['hstore'] != False and row[field['name']] != '':
                if n == 0:
                    string_2 = string_2 + ", other"
                    string_4 = string_4 + ", '"
                    n = n + 1
                string_4 = string_4 + f'''"{field['name']}" => "{row[field['name']]}", '''

        if n != 0:
            string_4 = string_4[:-2] + "'"

        exe_str = string_1 + string_2 + string_3 + string_4 + string_5
        print(exe_str)

        cur.execute(exe_str)

    conn.commit()
    cur.close()
    conn.close()

def update_record_metadata_catalogue_df(df, DBNAME, METADATA_CATALOGUE):

    conn = psycopg2.connect(f'dbname={DBNAME} user=' + getpass.getuser())
    cur = conn.cursor()

    for idx, row in df.iterrows():
        string_1 = f'UPDATE {METADATA_CATALOGUE} SET '
        string_2 = ''
        string_3 = ''
        string_4 = ''
        string_5 = f" WHERE id = '{row['id']}';"

        # MAIN FIELDS
        for field in fields.fields:
            if field['name'] in df.columns and field['hstore'] == False:
                if field['format'] in ['text', 'uuid', 'date', 'time', 'timestamp with time zone'] and str(row[field['name']]) != 'NULL':
                    string_2 = string_2 + field['name'] + ' = ' + "'" + str(row[field['name']]) + "'" + ', '
                else:
                    string_2 = string_2 + field['name'] + ' = ' + str(row[field['name']]) + ', '

        string_2 = string_2[:-2]

        # HSTORE FIELDS
        n = 0
        for field in fields.fields:
            if field['name'] in df.columns and field['hstore'] == 'other':
                if n == 0:
                    string_3 = string_3 + ", other = other || hstore(array["
                    string_4 = string_4 + "], array ["
                    n = n + 1
                string_3 = string_3 + f"'{field['name']}', "

                string_4 = string_4 + f"'{str(row[field['name']])}', "

        if n != 0:
            string_3 = string_3[:-2]
            string_4 = string_4[:-2] + "])"

        exe_str = string_1 + string_2 + string_3 + string_4 + string_5

        cur.execute(exe_str)

        # Removing hstore fields when value deleted when updating the record
        for field in fields.fields:
            if field['name'] in df.columns and field['hstore'] == 'other':
                if str(row[field['name']]) == '' or str(row[field['name']]) == 'NULL':
                    exe_str = f"UPDATE {METADATA_CATALOGUE} SET other = delete(other, '{field['name']}')"
                    cur.execute(exe_str)

    conn.commit()
    cur.close()
    conn.close()
