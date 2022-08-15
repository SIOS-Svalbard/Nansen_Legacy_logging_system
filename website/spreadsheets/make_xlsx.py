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
import os
from argparse import Namespace

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


def write_metadata(args, workbook, metadata_df):
    """
    Adds a metadata sheet to workbook
    Parameters
    ----------
    args : argparse object
        The input arguments
    workbook : xlsxwriter Workbook
        The workbook for the metadata sheet
    metadata_df: Pandas dataframe
        Pandas dataframe of filled-in metadata

    metadata_df: pandas.core.frame.DataFrame
        Optional parameter. Option to add metadata from a dataframe to the 'metadata' sheet.
    """

    sheet = workbook.add_worksheet('Metadata')

    metadata_fields = ['title', 'abstract', 'pi_name', 'pi_email', 'pi_institution',
                       'pi_address', 'recordedBy', 'projectID', 'cruiseNumber', 'vesselName']

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
    input_format = workbook.add_format({
        'bold': False,
        'font_name': DEFAULT_FONT,
        'text_wrap': True,
        'valign': 'left',
        'font_size': DEFAULT_SIZE
    })

    sheet.set_column(0, 0, width=30)
    sheet.set_column(2, 2, width=50)
    for ii, mfield in enumerate(metadata_fields):
        field = field_dict[mfield]
        sheet.write(ii, 0, field.disp_name, parameter_format)
        sheet.write(ii, 1, field.name, parameter_format)
        sheet.set_column(1, 1, None, None, {'hidden': True})

        if type(metadata_df) == pd.core.frame.DataFrame:
            try:
                sheet.write(ii,2,metadata_df[mfield][0], input_format)
            except:
                sheet.write(ii, 2, '', input_format)
                continue
        else:
            sheet.write(ii, 2, '', input_format)

        if field.validation:
            if args.verbose > 0:
                print("Writing metadata validation")
            valid_copy = field.validation.copy()
            if len(valid_copy['input_message']) > 255:
                valid_copy['input_message'] = valid_copy[
                    'input_message'][:252] + '...'
            sheet.data_validation(first_row=ii,
                                  first_col=2,
                                  last_row=ii,
                                  last_col=2,
                                  options=valid_copy)
            if field.cell_format:
                cell_format = workbook.add_format(field.cell_format)
                sheet.set_row(
                    ii, ii, cell_format=cell_format)

        if ii == 0:
            height = 30
        elif ii == 1: # Making abstract row height larger to encourage researches to write more.
            height = 150
        else:
            height = 15

        sheet.set_row(ii, height)

def make_xlsx(args, fields_list, metadata, conversions, data, metadata_df):
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
    """

    output = args.filepath
    workbook = xlsxwriter.Workbook(output)

    # Set font
    workbook.formats[0].set_font_name(DEFAULT_FONT)
    workbook.formats[0].set_font_size(DEFAULT_SIZE)

    if metadata:
        write_metadata(args, workbook, metadata_df)

    # Create sheet for data
    data_sheet = workbook.add_worksheet('Data')
    variable_sheet_obj = Variable_sheet(workbook)

    header_format = workbook.add_format({
        #         'bg_color': '#C6EFCE',
        'font_color': '#FF0000',
        'font_name': DEFAULT_FONT,
        'bold': False,
        'text_wrap': False,
        'valign': 'vcenter',
        #         'indent': 1,
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
    for idx, field in enumerate(fields.fields):
        if field['name'] in fields_list:
            # Write title row
            data_sheet.write(title_row, ii, field['disp_name'], field_format)

            # Write row below with parameter name
            data_sheet.write(parameter_row, ii, field['name'])

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

                print(field['name'],valid_copy, '\n')

                valid_copy['input_message'].replace('\n', '\n\r')

                if len(field['disp_name']) > 32:
                    valid_copy['input_title'] = field['disp_name'][:32]
                else:
                    valid_copy['input_title'] = field['disp_name']

                if 'long_list' in field.keys():

                    # Add the validation variable to the hidden sheet
                    ref = variable_sheet_obj.add_row(
                        field['name'], valid_copy['source'])
                    valid_copy.pop('source', None)
                    valid_copy['value'] = ref
                    field['description'].replace('\n', '\n\r')
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

    workbook.close()

def write_file(filepath, fields_list, metadata=True, conversions=True, data=False, metadata_df=False):
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
    """
    args = Namespace()
    args.verbose = 0
    args.dir = os.path.dirname(filepath)
    args.filepath = filepath

    make_xlsx(args, fields_list, metadata, conversions, data, metadata_df)
