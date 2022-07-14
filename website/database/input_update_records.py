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
    for field in fields.fields:
        if field['name'] in form_input.keys() and field['hstore'] == False:
            string_2 = string_2 + field['name'] +", "
            if field['format'] in ['text', 'uuid', 'date', 'time', 'timestamp with time zone'] and form_input[field['name']] != 'NULL':
                string_4 = string_4 + "'" + form_input[field['name']] + "'" + ", "
            else:
                string_4 = string_4 + form_input[field['name']] + ", "

    string_2 = string_2[:-2]
    string_4 = string_4[:-2]

    n = 0
    for field in fields.fields:
        if field['name'] in form_input.keys() and field['hstore'] != False:
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
    string_3 = f" WHERE id = '{form_input['id']}';"

    for field in fields.fields:
        if field['name'] in form_input.keys() and field['hstore'] == False:
            if field['format'] in ['text', 'uuid', 'date', 'time', 'timestamp with time zone'] and form_input[field['name']] != 'NULL':
                string_2 = string_2 + field['name'] + ' = ' + "'" + form_input[field['name']] + "'" + ', '
            else:
                string_2 = string_2 + field['name'] + ' = ' + form_input[field['name']] + ', '

    string_2 = string_2[:-2]

    exe_str = string_1 + string_2 + string_3

    cur.execute(exe_str)

    conn.commit()
    cur.close()
    conn.close()
