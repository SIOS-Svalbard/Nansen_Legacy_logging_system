import psycopg2
import psycopg2.extras
import pandas as pd

def insert_into_metadata_catalogue(fields_to_submit, num_records, DB, CRUISE_NUMBER):

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    for n in range(num_records):

        string_1 = f'INSERT INTO metadata_catalogue_{CRUISE_NUMBER} ('
        string_2 = ''
        string_3 = ') VALUES ('
        string_4 = ''
        string_5 = ');'

        # MAIN FIELDS
        for field, criteria in fields_to_submit['columns'].items():
            string_2 = string_2 + field +", "
            if type(criteria['value']) == list:
                v = criteria['value'][n]
                if not v and v != 0:
                    v = 'NULL'
            else:
                v = criteria['value']
            if criteria['format'] in ['text', 'uuid', 'date', 'time', 'timestamp with time zone'] and v != 'NULL':
                string_4 = f"{string_4}'{v}', "
            else:
                string_4 = f"{string_4}{v}, "


        string_2 = string_2[:-2]
        string_4 = string_4[:-2]

        # HSTORE FIELDS
        N = 0
        for field, criteria in fields_to_submit['hstore'].items():
            if type(criteria['value']) == list:
                v = criteria['value'][n]
            else:
                v = criteria['value']
            if v != '':
                if N == 0:
                    string_2 = string_2 + ", other"
                    string_4 = string_4 + ", '"
                    N = N + 1
                string_4 = string_4 + f'''"{field}" => "{v}", '''

        if N != 0:
            string_4 = string_4[:-2] + "'"

        exe_str = string_1 + string_2 + string_3 + string_4 + string_5
        cur.execute(exe_str)

    conn.commit()
    cur.close()
    conn.close()

def update_record_metadata_catalogue(fields_to_submit, DB, CRUISE_NUMBER, IDs):

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    for n in range(len(IDs)):

        string_1 = f'UPDATE metadata_catalogue_{CRUISE_NUMBER} SET '
        string_2 = ''
        string_3 = ''
        string_4 = ''
        string_5 = f" WHERE id = '{IDs[n]}';"

        # MAIN FIELDS
        for field, criteria in fields_to_submit['columns'].items():
            if 'value' in criteria:
                if type(criteria['value']) == list:
                    v = criteria['value'][n]
                    if not v and v != 0:
                        v = 'NULL'
                else:
                    v = criteria['value']
                if criteria['format'] in ['text', 'uuid', 'date', 'time', 'timestamp with time zone'] and criteria['value'] != 'NULL':
                    string_2 = f"{string_2} {field} = '{v}', "
                else:
                    string_2 = f"{string_2} {field} = {v}, "

        string_2 = string_2[:-2]

        # HSTORE FIELDS
        N = 0
        for field, criteria in fields_to_submit['hstore'].items():
            if 'value' in criteria:
                if type(criteria['value']) == list:
                    v = criteria['value'][n]
                else:
                    v = criteria['value']
                if v != '':
                    if N == 0:
                        string_3 = string_3 + ", other = other || hstore(array["
                        string_4 = string_4 + "], array ["
                        N = N + 1
                    string_3 = string_3 + f"'{field}', "

                    string_4 = string_4 + f"'{v}', "

        if N != 0:
            string_3 = string_3[:-2]
            string_4 = string_4[:-2] + "])"

        exe_str = string_1 + string_2 + string_3 + string_4 + string_5
        cur.execute(exe_str)

        # Removing hstore fields when value deleted when updating the record
        for field, criteria in fields_to_submit['hstore'].items():
            if type(criteria['value']) == list:
                if criteria['value'][n] in ['', 'NULL', None]:
                    exe_str = f"UPDATE metadata_catalogue_{CRUISE_NUMBER} SET other = delete(other, '{field}')"
                    cur.execute(exe_str)
            else:
                if criteria['value'] in ['', 'NULL', None]:
                    exe_str = f"UPDATE metadata_catalogue_{CRUISE_NUMBER} SET other = delete(other, '{field}')"
                    cur.execute(exe_str)

    conn.commit()
    cur.close()
    conn.close()
