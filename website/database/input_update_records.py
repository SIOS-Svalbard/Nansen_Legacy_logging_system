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

    '''
    reorder form_input so that hstore fields are at the end
    write fields to string_2
    write values to string_4
    write both without hstore firstly, add hstores after
    '''
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

    # update {METADATA_CATALOGUE} SET other = hstore(array['new_users','post_count'], array[p_user_count, p_post_count]::text[]) WHERE ...
    # See https://stackoverflow.com/questions/33230536/update-postgresql-hstore-field-with-sql-variable
    # need to pull all existing hstore values and rewrite them in the update, otherwise they will disappear

    for field in fields.fields:
        if field['name'] in form_input.keys() and field['hstore'] == False:
            if field['format'] in ['text', 'uuid', 'date', 'time', 'timestamp with time zone'] and form_input[field['name']] != 'NULL':
                string_2 = string_2 + field['name'] + ' = ' + "'" + form_input[field['name']] + "'" + ', '
            else:
                string_2 = string_2 + field['name'] + ' = ' + form_input[field['name']] + ', '

    string_2 = string_2[:-2]

    # NEED TO TEST THE HSTORE BIT
    n = 0
    for field in fields.fields:
        if field['name'] in form_input.keys() and field['hstore'] == 'other': # and form_input[field['name']] != '':? What about when removing a field from hstore?
            if n == 0:
                string_3 = string_3 + ", other = hstore (array["
                string_4 = string_4 + "], array ["
                n = n + 1
            string_3 = string_3 + "'" + f"{field['name']}" + "', "
            string_4 = string_4 + form_input[field['name']] + ', '
    if n != 0:
        string_3 = string_3[:-2]
        string_4 = string_4[:-2] + "]::text[])"

    exe_str = string_1 + string_2 + string_3 + string_4 + string_5

    print('STRING HERE')
    print(exe_str)
    print('END HERE')
    cur.execute(exe_str)

    conn.commit()
    cur.close()
    conn.close()
