#!/usr/bin/python3
# encoding: utf-8
'''
 -- Creates xlsx files for logging samples or sampling activities
@author:     Luke Marsden
@contact:    lukem@unis.no

Based on https://github.com/SIOS-Svalbard/darwinsheet/blob/master/scripts/make_xlsx.py
'''

import xlsxwriter
import pandas as pd
import website.database.fields as fields
import website.database.metadata_fields as metadata_fields
import os
from argparse import Namespace
from website.database.get_data import get_data, get_personnel_list

DEBUG = 1

DEFAULT_FONT = 'Calibri'
DEFAULT_SIZE = 10


class Variable_sheet(object):
    """
    Class for handling the variable sheet
    """

    def __init__(self, workbook):
        """
        Initialises the sheet
        Parameters
        ----------
        workbook: Xlsxwriter workbook
            The parent workbook where the sheet is added
        """
        self.workbook = workbook
        self.name = 'Variables'  # The name of the worksheet
        self.sheet = workbook.add_worksheet(self.name)
        self.sheet.hide()  # Hide the sheet
        # For holding the current row to add variables on
        self.current_column = 0

    def add_row(self, variable, parameter_list):
        """
        Adds a row of parameters to a variable and returns the ref for the list
        Parameters
        ----------
        variable : str
            The name of the variable
        parameter_list :
            List of parameters to be added
        Returns
        ----------
        ref : str
            The range of the list in Excel format
        """

        self.sheet.write(0, self.current_column, variable)
        name = 'Table_' + variable.replace(' ', '_').capitalize()

        self.sheet.add_table(
            1, self.current_column,
            1 + len(parameter_list), self.current_column,
            {'name': name,
                'header_row': 0}
        )

        for ii, par in enumerate(sorted(parameter_list, key=str.lower)):
            self.sheet.write(1 + ii, self.current_column, par)
        ref = '=INDIRECT("' + name + '")'

        # Increment row such that the next gets a new row
        self.current_column = self.current_column + 1
        return ref


def make_dict_of_fields():
    """
    Makes a dictionary of the possible fields.
    Does this by reading the fields list from the fields.py library
    Returns
    ---------
    field_dict : dict
        Dictionary of the possible fields
        Contains a Field object under each name
    """

    field_dict = {}
    for field in fields.fields:
        field['name'] = field['name']
        new = Field(field['name'], field['disp_name'])
        if 'valid' in field:
            new.set_validation(field['valid'])
        if 'cell_format' in field:
            new.set_cell_format(field['cell_format'])
        if 'width' in field:
            new.set_width(field['width'])
        else:
            new.set_width(len(field['disp_name']))
        if 'long_list' in field:
            new.set_long_list(field['long_list'])

        field_dict[field['name']] = new
    return field_dict

def derive_content(mfield, DBNAME=False, CRUISE_DETAILS_TABLE=False, METADATA_CATALOGUE=False):
    '''
    Derives values for the metadata sheet
    based on metadata catalogue or cruise details table

    Parameters
    ----------
    mfield: dictionary
        Dictionary of the field
    DBNAME: string
        Name of the database where the metadata catalogue is hosted
        Default: False, for when template generate used independent of the database
    METADATA_CATALOGUE: string
        Name of the table of the metadata catalogue for the cruise
        Default: False, for when template generate used independent of the database
    CRUISE_DETAILS_TABLE: string
        Name of the table of the cruise details for the cruise
        Default: False, for when template generate used independent of the database

    Returns
    ----------
    Content of the field to be printed on the metadata sheet upon creation
    '''


    if DBNAME == False:
        content = ''

    elif 'derive_from_table' in mfield.keys():
        if mfield['derive_from_table'] == 'cruise_details':
            df = get_data(DBNAME, CRUISE_DETAILS_TABLE)
            content = df[mfield['name']][0]
        else:
            content = ''

    else:
        content = 'STILL NEED TO DERIVE, SEE MAKE_XLSX.PY FILE, DERIVE_CONTENT FUNCTION'

    return content

def write_conversion(args, workbook):
    """
    Adds a conversion sheet to workbook
    Parameters
    ----------
    args : argparse object
        The input arguments
    workbook : xlsxwriter Workbook
        The workbook for the conversion sheet
    """

    sheet = workbook.add_worksheet('Conversion')

    parameter_format = workbook.add_format({
        'font_name': DEFAULT_FONT,
        'right': True,
        'bottom': True,
        'bold': False,
        'text_wrap': True,
        'valign': 'left',
        'font_size': DEFAULT_SIZE + 2,
        'bg_color': '#B9F6F5',
    })
    center_format = workbook.add_format({
        'font_name': DEFAULT_FONT,
        'right': True,
        'bottom': True,
        'bold': False,
        'text_wrap': True,
        'valign': 'center',
        'font_size': DEFAULT_SIZE + 2,
        'bg_color': '#23EEFF',
    })
    output_format = workbook.add_format({
        'font_name': DEFAULT_FONT,
        'right': True,
        'bottom': True,
        'bold': False,
        'text_wrap': True,
        'valign': 'left',
        'font_size': DEFAULT_SIZE + 2,
        'bg_color': '#FF94E8',
    })

    sheet.set_column(0, 2, width=30)

    sheet.write(1, 0, "Coordinate conversion ", parameter_format)
    sheet.merge_range(2, 0, 2, 1, "Degree Minutes Seconds ", center_format)
    sheet.write(3, 0, "Degrees ", parameter_format)
    sheet.write(4, 0, "Minutes ", parameter_format)
    sheet.write(5, 0, "Seconds ", parameter_format)
    sheet.write(6, 0, "Decimal degrees ", output_format)
    sheet.write(6, 1, "=B4+B5/60+B6/3600 ", output_format)
    sheet.merge_range(7, 0, 7, 1, "Degree decimal minutes", center_format)
    sheet.write(8, 0, "Degrees ", parameter_format)
    sheet.write(9, 0, "Decimal minutes ", parameter_format)
    sheet.write(10, 0, "Decimal degrees ", output_format)
    sheet.write(10, 1, "=B9+B10/60 ", output_format)

def write_readme(args, workbook):
    """
    Adds a README sheet to workbook
    Parameters
    ----------
    args : argparse object
        The input arguments
    workbook : xlsxwriter Workbook
        The workbook for the README sheet
    """

    sheet = workbook.add_worksheet('README')

    sheet.set_column(0, 2, width=30)

    header_format = workbook.add_format({
        'font_name': DEFAULT_FONT,
        'right': True,
        'bottom': True,
        'bold': True,
        'text_wrap': True,
        'valign': 'center',
        'font_size': 25,
        'bg_color': '#B9F6F5',
    })

    sheet.write(1, 0, "README", header_format)
    sheet.set_row(1, 30)

def write_metadata(args, workbook, metadata_df, DBNAME=False, CRUISE_DETAILS_TABLE=False, METADATA_CATALOGUE=False):
    """
    Adds a metadata sheet to workbook
    Parameters
    ----------
    args : argparse object
        The input arguments
    workbook : xlsxwriter Workbook
        The workbook for the metadata sheet
    metadata_df: pandas.core.frame.DataFrame
        Optional parameter. Option to add metadata from a dataframe to the 'metadata' sheet.
    DBNAME: string
        Name of the database where the metadata catalogue is hosted
        Default: False, for when template generate used independent of the database
    METADATA_CATALOGUE: string
        Name of the table of the metadata catalogue for the cruise
        Default: False, for when template generate used independent of the database
    CRUISE_DETAILS_TABLE: string
        Name of the table of the cruise details for the cruise
        Default: False, for when template generate used independent of the database
    """

    sheet = workbook.add_worksheet('Metadata')

    header_format = workbook.add_format({
        'font_name': DEFAULT_FONT,
        'font_color': '#FFFFFF',
        'right': True,
        'bottom': 5,
        'bold': True,
        'text_wrap': True,
        'valign': 'vcenter',
        'font_size': DEFAULT_SIZE + 2,
        'bg_color': '#4a4a4a',
    })

    parameter_format = workbook.add_format({
            'font_name': DEFAULT_FONT,
            'bottom': True,
            'right': True,
            'bold': False,
            'text_wrap': True,
            'valign': 'vcenter',
            'font_size': DEFAULT_SIZE + 1,
            'bg_color': '#B9F6F5'
        })

    blank_format = workbook.add_format({
        'bold': False,
        'font_name': DEFAULT_FONT,
        'text_wrap': True,
        'valign': 'vcenter',
        'bottom': True,
        'right': True,
        'font_size': DEFAULT_SIZE,
        })

    hidden_col_format = workbook.add_format({
        'bold': False,
        'font_name': DEFAULT_FONT,
        'text_wrap': True,
        'valign': 'vcenter',
        'bottom': True,
        'right': 5,
        'font_size': DEFAULT_SIZE,
        })

    input_optional_format = workbook.add_format({
        'bold': False,
        'font_name': DEFAULT_FONT,
        'text_wrap': True,
        'valign': 'vcenter',
        'bottom': True,
        'right': 5,
        'font_size': DEFAULT_SIZE,
        'left': 5
        })

    input_datetime_format = workbook.add_format({
        'bold': False,
        'font_name': DEFAULT_FONT,
        'text_wrap': True,
        'valign': 'vcenter',
        'bottom': True,
        'right': 5,
        'font_size': DEFAULT_SIZE,
        'left': 5,
        'num_format': 'yyyy-mm-ddThh:mm:ssZ'
        })

    input_required_format = workbook.add_format({
            'font_name': DEFAULT_FONT,
            'bottom': True,
            'bold': False,
            'text_wrap': True,
            'valign': 'vcenter',
            'font_size': DEFAULT_SIZE,
            'bg_color': '#F5E69E',
            'left': 5,
            'right': 5
        })

    input_required_key_format = workbook.add_format({
            'font_name': DEFAULT_FONT,
            'bottom': True,
            'bold': False,
            'text_wrap': True,
            'valign': 'vcenter',
            'font_size': DEFAULT_SIZE,
            'bg_color': '#F5E69E',
            'left': True,
            'right': True
        })

    acdd_highly_recommended_format = workbook.add_format({
            'font_name': DEFAULT_FONT,
            'bottom': True,
            'right': True,
            'bold': False,
            'text_wrap': True,
            'valign': 'vcenter',
            'font_size': DEFAULT_SIZE,
            'bg_color': '#F06292'
        })

    acdd_recommended_format = workbook.add_format({
            'font_name': DEFAULT_FONT,
            'bottom': True,
            'right': True,
            'bold': False,
            'text_wrap': True,
            'valign': 'vcenter',
            'font_size': DEFAULT_SIZE,
            'bg_color': '#F8BBD0'
        })

    acdd_suggested_format = workbook.add_format({
            'font_name': DEFAULT_FONT,
            'bottom': True,
            'right': True,
            'bold': False,
            'text_wrap': True,
            'valign': 'vcenter',
            'font_size': DEFAULT_SIZE,
            'bg_color': '#F5E1E8'
        })


    eml_required_format = workbook.add_format({
            'font_name': DEFAULT_FONT,
            'bottom': True,
            'right': True,
            'bold': False,
            'text_wrap': True,
            'valign': 'vcenter',
            'font_size': DEFAULT_SIZE,
            'bg_color': '#AED581'
        })

    eml_optional_format = workbook.add_format({
            'font_name': DEFAULT_FONT,
            'bottom': True,
            'right': True,
            'bold': False,
            'text_wrap': True,
            'valign': 'vcenter',
            'font_size': DEFAULT_SIZE,
            'bg_color': '#DCEDC8'
        })

    bottom_border_format = workbook.add_format({
        'bold': False,
        'font_name': DEFAULT_FONT,
        'text_wrap': True,
        'valign': 'vcenter',
        'top': 5,
        'font_size': DEFAULT_SIZE,
        })

    cols = [
            'Field name',
            'systemName',
            'Content',
            'ACDD term',
            'ACDD description',
            'EML term',
            'EML description'
            'Link'
            ]

    header_row = 5
    start_row = header_row + 2

    for ii, col in enumerate(cols):
        sheet.write(header_row, ii, col, header_format)
        sheet.write(header_row+1, ii, col, blank_format)
        sheet.set_row(header_row+1, None, None, {'hidden': True})

    metadata_fields_df = pd.DataFrame(columns=(cols))

    for ii, mfield in enumerate(metadata_fields.metadata_fields):

        row = start_row + ii

        if 'acdd' in mfield.keys():
            acdd_term = mfield['acdd']['name']
            acdd_description = mfield['acdd']['description']
            if mfield['acdd']['recommendations'] == 'Highly Recommended':
                acdd_format = acdd_highly_recommended_format
            elif mfield['acdd']['recommendations'] == 'Recommended':
                acdd_format = acdd_recommended_format
            else:
                acdd_format = acdd_suggested_format
        else:
            acdd_term = ''
            acdd_description = ''
            acdd_format = blank_format

        if 'eml' in mfield.keys():
            eml_term = mfield['eml']['name']
            eml_description = mfield['eml']['description']
            if mfield['eml']['recommendations'] == 'Required':
                eml_format = eml_required_format
            else:
                eml_format = eml_optional_format
        else:
            eml_term = ''
            eml_description = ''
            eml_format = blank_format

        if mfield['required'] == True:
            input_format = input_required_format
        elif mfield['format'] == 'datetime':
            input_format = input_datetime_format
        else:
            input_format = input_optional_format

        if 'default' in mfield.keys():
            content = mfield['default']
        elif 'derive_from' in mfield.keys():
            content = derive_content(mfield, DBNAME, CRUISE_DETAILS_TABLE, METADATA_CATALOGUE)
        else:
            content = ''

        if 'link' in mfield.keys():
            link = mfield['link']
        else:
            link = ''

        # Column A: Display name
        sheet.write(row, 0, mfield['disp_name'], parameter_format)

        # Column B (hidden): System field name
        sheet.write(row, 1, mfield['name'], hidden_col_format)
        sheet.set_column(1, 1, None, None, {'hidden': True})

        # Column C: Content
        if type(metadata_df) == pd.core.frame.DataFrame:
            try:
                sheet.write(row,2,metadata_df[mfield][0], input_format)
            except:
                sheet.write(row, 2, content, input_format)
                continue
        else:
            sheet.write(row, 2, content, input_format)

        if 'valid' in mfield.keys():
            valid_copy = mfield['valid'].copy()

            if len(valid_copy['input_message']) > 255:
                valid_copy['input_message'] = valid_copy[
                    'input_message'][:252] + '...'

            if len(mfield['disp_name']) > 32:
                valid_copy['input_title'] = mfield['disp_name'][:32]
            else:
                valid_copy['input_title'] = mfield['disp_name']

            if 'long_list' in mfield.keys():

                # Add the validation variable to the hidden sheet
                lst_values = mfield['valid']['source']

                ref = variable_sheet_obj.add_row(
                    mfield['name'], lst_values)

                valid_copy.pop('source', None)
                valid_copy['value'] = ref

            sheet.data_validation(first_row=row,
                                  first_col=2,
                                  last_row=row,
                                  last_col=2,
                                  options=valid_copy)

        # Column D: ACDD name
        sheet.write(row, 3, acdd_term, acdd_format)

        # Column E: ACDD description
        sheet.write(row, 4, acdd_description, acdd_format)

        # Column F: EML name
        sheet.write(row, 5, eml_term, eml_format)

        # Column G: EML description
        sheet.write(row, 6, eml_description, eml_format)

        # Column H: Link
        sheet.write(row, 7, link, blank_format)

        length = max([len(acdd_description), len(eml_description)])

        if mfield['name'] == 'summary':
            height = 150
        elif length > 0:
            height = int(length/4)
        else:
            height = 15

        sheet.set_row(row, height)

    for col in range(len(cols)):
        sheet.write(row+1, col,'',bottom_border_format)

    sheet.merge_range('C2:C4', 'Required for metadata catalogue', input_required_key_format)

    sheet.merge_range('D2:E2', 'Highly recommended ACDD term', acdd_highly_recommended_format)
    sheet.merge_range('D3:E3', 'Recommended ACDD term', acdd_recommended_format)
    sheet.merge_range('D4:E4', 'Suggested ACDD term', acdd_suggested_format)

    sheet.merge_range('F2:G2', 'Required EML term', eml_required_format)
    sheet.merge_range('F3:G3', 'Optional EML term', eml_optional_format)

    sheet.set_column(0, 0, width=20)
    sheet.set_column(2, 2, width=40)
    sheet.set_column(3, 3, width=20)
    sheet.set_column(4, 4, width=60)
    sheet.set_column(5, 5, width=20)
    sheet.set_column(6, 6, width=60)
    sheet.set_column(7, 7, width=60)

    # Freeze the rows at the top
    sheet.freeze_panes(6, 1)

def make_xlsx(args, fields_list, metadata, conversions, data, metadata_df, DBNAME, CRUISE_DETAILS_TABLE=False, METADATA_CATALOGUE=False):
    """
    Writes the xlsx file based on the wanted fields
    Parameters
    ----------
    args : argparse object
        The input arguments
    fields_list : list
        A list of the wanted fields
    metadata: Boolean
        Should the metadata sheet be written
    conversions: Boolean
        Should the conversions sheet be written

    data: pandas.core.frame.DataFrame
        Optional parameter. Option to add data from a dataframe to the 'data' sheet.

    metadata_df: pandas.core.frame.DataFrame
        Optional parameter. Option to add metadata from a dataframe to the 'metadata' sheet.
    DBNAME: string
        Name of the database where the metadata catalogue is hosted
        Default: False, for when template generate used independent of the database
    METADATA_CATALOGUE: string
        Name of the table of the metadata catalogue for the cruise
        Default: False, for when template generate used independent of the database
    CRUISE_DETAILS_TABLE: string
        Name of the table of the cruise details for the cruise
        Default: False, for when template generate used independent of the database
    """

    output = args.filepath
    workbook = xlsxwriter.Workbook(output)

    # Set font
    workbook.formats[0].set_font_name(DEFAULT_FONT)
    workbook.formats[0].set_font_size(DEFAULT_SIZE)

    if metadata:
        write_metadata(args, workbook, metadata_df, DBNAME, CRUISE_DETAILS_TABLE, METADATA_CATALOGUE)

    # Create sheet for data
    data_sheet = workbook.add_worksheet('Data')
    variable_sheet_obj = Variable_sheet(workbook)

    header_format = workbook.add_format({
        'font_color': '#FF0000',
        'font_name': DEFAULT_FONT,
        'bold': False,
        'text_wrap': False,
        'valign': 'vcenter',
        'font_size': DEFAULT_SIZE + 2
    })

    field_format = workbook.add_format({
        'font_name': DEFAULT_FONT,
        'bottom': True,
        'right': True,
        'bold': False,
        'text_wrap': True,
        'valign': 'vcenter',
        'font_size': DEFAULT_SIZE + 1,
        'bg_color': '#B9F6F5'
    })

    date_format = workbook.add_format({
        'font_name': DEFAULT_FONT,
        'bold': False,
        'text_wrap': False,
        'valign': 'vcenter',
        'font_size': DEFAULT_SIZE,
        'num_format': 'dd/mm/yy'
        })

    time_format = workbook.add_format({
        'font_name': DEFAULT_FONT,
        'bold': False,
        'text_wrap': False,
        'valign': 'vcenter',
        'font_size': DEFAULT_SIZE,
        'num_format': 'hh:mm:ss'
        })

    title_row = 1  # starting row
    start_row = title_row + 2
    parameter_row = title_row + 1  # Parameter row, hidden
    end_row = 20000  # ending row

    # Loop over all the variables needed
    ii = 0

    for field in fields.fields:
        if field['name'] in fields_list:

            if field['name'] in ['pi_details','recordedBy_details']:
                duplication = 3 # 3 copies of these columns
            else:
                duplication = 1 # One copy of all other columns

            while duplication > 0:

                # Write title row
                data_sheet.write(title_row, ii, field['disp_name'], field_format)

                # Write row below with parameter name
                data_sheet.write(parameter_row, ii, field['name']+ '_' + str(duplication))

                # Write validation
                if 'valid' in field.keys():

                    if args.verbose > 0:
                        print("Writing validation for", field['name'])

                    # Need to make sure that 'input_message' is not more than 255
                    valid_copy = field['valid'].copy()
                    if len(field['description']) > 255:
                        valid_copy['input_message'] = field['description'][:252] + '...'
                    else:
                        valid_copy['input_message'] = field['description']

                    valid_copy['input_message'].replace('\n', '\n\r')

                    if len(field['disp_name']) > 32:
                        valid_copy['input_title'] = field['disp_name'][:32]
                    else:
                        valid_copy['input_title'] = field['disp_name']

                    if 'long_list' in field.keys():

                        # Add the validation variable to the hidden sheet
                        table = valid_copy['source']
                        if DBNAME == False:
                            df = pd.read_csv(f'website/database/{table}.csv')
                        else:
                            df = get_data(DBNAME, table)

                        if field['name'] in ['pi_details', 'recordedBy_details']:
                            lst_values = get_personnel_list(DBNAME=DBNAME, table='personnel')
                        else:
                            print(df.columns)
                            lst_values = list(df[field['name'].lower()])

                        ref = variable_sheet_obj.add_row(
                            field['name']+str(duplication), lst_values)

                        valid_copy.pop('source', None)
                        valid_copy['value'] = ref

                        data_sheet.data_validation(first_row=start_row,
                                                   first_col=ii,
                                                   last_row=end_row,
                                                   last_col=ii,
                                                   options=valid_copy)

                    else:

                        data_sheet.data_validation(first_row=start_row,
                                                   first_col=ii,
                                                   last_row=end_row,
                                                   last_col=ii,
                                                   options=valid_copy)

                if 'cell_format' in field.keys():
                    if 'font_name' not in field['cell_format']:
                        field['cell_format']['font_name'] = DEFAULT_FONT
                    if 'font_size' not in field['cell_format']:
                        field['cell_format']['font_size'] = DEFAULT_SIZE
                    cell_format = workbook.add_format(field['cell_format'])
                    data_sheet.set_column(
                        ii, ii, width=20, cell_format=cell_format)
                else:
                    data_sheet.set_column(first_col=ii, last_col=ii, width=20)

                ii = ii + 1
                duplication = duplication - 1

    # Write optional data to data sheet
    if type(data) == pd.core.frame.DataFrame:
        for col_num, field in enumerate(data):
            try:
                if field in ['eventDate', 'start_date', 'end_date']:
                    data_sheet.write_column(start_row,col_num,list(data[field]), date_format)
                elif field in ['eventTime', 'start_time', 'end_time']:
                    data_sheet.write_column(start_row,col_num,list(data[field]), time_format)
                else:
                    data_sheet.write_column(start_row,col_num,list(data[field]))
            except:
                pass

    # Add header, done after the other to get correct format
    data_sheet.write(0, 0, '', header_format)
    # Add hint about pasting
    data_sheet.merge_range(0, 1, 0, 7,
                           "When pasting only use 'paste special' / 'paste only', selecting numbers and/or text ",
                           header_format)
    # Set height of row
    data_sheet.set_row(0, height=24)

    # Freeze the rows at the top
    data_sheet.freeze_panes(start_row, 0)

    # Hide ID row
    data_sheet.set_row(parameter_row, None, None, {'hidden': True})

    if conversions:
        write_conversion(args, workbook)

    write_readme(args, workbook)

    workbook.close()

def write_file(filepath, fields_list, metadata=True, conversions=True, data=False, metadata_df=False, DBNAME=False, CRUISE_DETAILS_TABLE=False, METADATA_CATALOGUE=False):
    """
    Method for calling from other python programs
    Parameters
    ----------
    filepath: string
        The output file
    fields_list : list
        A list of the wanted fields
    metadata: Boolean
        Should the metadata sheet be written
        Default: True
    conversions: Boolean
        Should the conversions sheet be written
        Default: True
    data: pandas.core.frame.DataFrame
        Optional parameter. Option to add data from a dataframe to the 'data' sheet.
        Default: False
    metadata_df: pandas.core.frame.DataFrame
        Optional parameter. Option to add metadata from a dataframe to the 'metadata' sheet.
        Default: False
    DBNAME: string
        Name of the database where the metadata catalogue is hosted
        Default: False, for when template generate used independent of the database
    METADATA_CATALOGUE: string
        Name of the table of the metadata catalogue for the cruise
        Default: False, for when template generate used independent of the database
    CRUISE_DETAILS_TABLE: string
        Name of the table of the cruise details for the cruise
        Default: False, for when template generate used independent of the database
    """
    args = Namespace()
    args.verbose = 0
    args.dir = os.path.dirname(filepath)
    args.filepath = filepath

    make_xlsx(args, fields_list, metadata, conversions, data, metadata_df, DBNAME, CRUISE_DETAILS_TABLE, METADATA_CATALOGUE)
