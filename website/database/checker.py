#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Checks data before they can be imported into the metadata catalogue

@author: lukem
"""

import pandas as pd
import datetime
from datetime import datetime as dt
import numpy as np
import requests
import psycopg2
import getpass
from website.database.get_data import get_data, get_registered_activities
import website.database.fields as fields
from website.other_functions.other_functions import split_personnel_list
import uuid

def make_valid_dict(DBNAME):
    """
    Makes a dictionary of the possible fields with their validation.
    Does this by reading the fields list from the fields.py library, the
    dwcterms.rdf (Darwin core) file  and dcterms.rdf (Dublin Core)
    Returns
    ---------
    field_dict : dict
        Dictionary of the possible fields
        Contains a Checker object under each name
    """
    # First we go through the fields.py
    field_dict = {}
    for field in fields.fields:
        new = Checker(DBNAME, name=field['name'], disp_name=field['disp_name'])
        if 'valid' in field:
            new.set_validation(DBNAME, field['valid'])
        if 'inherit' in field:
            new.inherit = field['inherit']
        if 'units' in field:
            new.units = field['units']
        field_dict[field['name']] = new

    return field_dict

def format_num(num):
    """
    Convert a string with a number to a number by removing common mistakes
    in Excel.
    Converts ',' to '.'
    Removes leading "'"
    If resulting string can be converted to an int, it is returned as an int,
    if not, it is returned as a float. If it can not be converted to a float,
    it throws a ValueError.
    Parameters
    ---------
    num: object
        The number to be converted.
        If it is an int or float, nothing is done with it.
        Needs to be convertible into a string.
    Returns
    ---------
    out: int or float
        The resulting int or float.
    """

    if isinstance(num, int) or isinstance(num, float):
        return num

    num_str = str(num).replace(',', '.').replace("'", '')

    try:
        out = int(num_str)
    except ValueError:
        out = float(num_str)
    return out


def is_nan(value):
    """
    Checks if value is 'nan' or NaT
    Parameters
    ---------
    value: object
        The object to be checked that it is not nan
    Returns
    ---------
    isnan: Boolean
        True: nan
        False: not nan
    """
    isnan = str(value).lower() == 'nan'
    isnat = str(value).lower() == 'nat'
    return isnan or isnat

class Evaluator(object):
    """ An object for holding a function for evaluating a type of data.
    The function should take two arguments, self and a value. By referencing and
    setting values on the object with self, it is possible to evaluate on
    multiple conditions."""

    def __init__(self, validation, func=None):
        """
        Initialise the Evaluator object.
        Parameters
        ---------
        validation: dict
            A dict containing the validation information.
            Can be used in evaluator function by referencing the property
            self.validation
        func: lambda function, optional
            This function should take two inputs, self and a value.
            If this is not set here, it needs to be set using the set_func
            method
            Should return a boolean, where True means the value has passed the
            test
            An example of a functions is:
            lambda self,x : self.valid['value'] < len(x)
        """

        self.validation = validation
        self.eval = func

    def set_func(self, func):
        """
        Method for setting the evaluator function.
        Parameters
        ---------
        func: lambda function, optional
            This function should take two inputs, self and a value.
            If this is not set here, it needs to be set using the set_func
            method
            Should return a boolean, where True means the value has passed the
            test
            An example of a functions is:
            lambda self, x : self.valid['value'] < len(x)
        """

        self.eval = func

    def evaluate(self, value):
        """
        Evaluate value with the evaluator
        Parameters
        ---------
        value: object
            The value to be evaluated
            Needs to be in a format that the function understands
        Returns
        ---------
        res: Boolean
            The result from the evaluator
            True, means that the value passed the evaluation
        """

        if self.eval == None:
            raise NameError(
                "No evaluator, set it during initialisation or with the 'set_func' method")
        try:
            res = self.eval(self, value)
        except TypeError:
            res = False
        if not(isinstance(res, bool)):
            raise ValueError(
                "The evaluator function is not returning a boolean")
        return res

class Field(object):
    """
    Object for holding the specification of a cell
    """

    def __init__(self, name, disp_name, validation={},
                 cell_format={}, width=20, long_list=False):
        """
        Initialising the object
        Parameters
        ----------
        name : str
               Name of object
        disp_name : str
               The title of the column
        validation : dict, optional
            A dictionary using the keywords defined in xlsxwriter
        cell_format : dict, optional
            A dictionary using the keywords defined in xlsxwriter
        width : int, optional
            Number of units for width
        long_list : Boolean, optional
            True for enabling the long list.
        """
        self.name = name  # Name of object
        self.disp_name = disp_name  # Title of column
        self.cell_format = cell_format  # For holding the formatting of the cell
        self.validation = validation  # For holding the validation of the cell
        self.long_list = long_list  # For holding the need for an entry in the
        # variables sheet
        self.width = width

    def set_validation(self, validation):
        """
        Set the validation of the cell
        Parameters
        ----------
        validation : dict
            A dictionary using the keywords defined in xlsxwriter
        """
        self.validation = validation

    def set_cell_format(self, cell_format):
        """
        Set the validation of the cell
        Parameters
        ----------
        cell_format : dict
            A dictionary using the keywords defined in xlsxwriter
        """
        self.cell_format = cell_format

    def set_width(self, width):
        """
        Set the cell width
        Parameters
        ----------
        width : int
            Number of units for width
        """
        self.width = width

    def set_long_list(self, long_list):
        """
        Set the need for moving the source in the list to a cell range in the
        variables sheet
        Parameters
        ----------
        long_list : Boolean
            True for enabling the long list.
        """
        self.long_list = long_list

class Checker(Field):
    """
    Object for holding the specification of a cell, and the validation of it
    Inherits from Field"""

    def __init__(self, DBNAME, inherit=False, units=None, *args, **kwargs):
        """
        Initialising the object
        Parameters
        ---------
        inherit: Boolean, optional
            Should the given field be inherited.
            Default: False
        units: string, optional
            The units of the field
        *args: arguments for Field
        **kwargs: keyword arguments for Field
        """
        Field.__init__(self, *args, **kwargs)
        if self.validation != {}:
            self.validator = self.get_validator(DBNAME, self.validation)
        else:
            self.validator = lambda x: True

        self.inherit = inherit
        self.units = units

    def set_validation(self, DBNAME, validation):
        """
        Method for setting the validation by reading the dictionary
        and converting it using the
        Parameters
        ---------
        validation: dict
            The specifications of the validation as a dict
            See the valid dict in Fields for details
        """

        Field.set_validation(self, validation)
        self.validator = self.get_validator(DBNAME, self.validation)

    def get_validator(self, DBNAME, validation=None):
        """
        Checks a parameter according to the defined validation
        Parameters
        ---------
        validation: dict, optional
            The valid dictionary defined in the fields.py file
            If not set, reads from the object
        Returns
        ---------
        validator: Evaluator
            A validator in the form of an Evaluator object
        """

        if validation == None:
            validation = self.validation

        validate = validation['validate']
        if validate == 'any':
            return Evaluator(validation, func=lambda self, x: isinstance(str(x), str))
        elif validate == 'list' and DBNAME != False:
            table = validation['source']
            df = get_data(DBNAME, table)
            lst = df[self.name.lower()].values
            return Evaluator(lst, func=lambda self, x: str(x) in self.validation)

        criteria = validation['criteria']

        def _formula_to_date(formula):
            """
            Internal function for converting validation date functions (Excel
            function) to a datetime date object
            Parameters
            ---------
            formula: str
                The Excel formula to be converted
                Supports simple addition and subtraction and the function TODAY
            Returns
            ---------
            date: datetime date object
                The resulting date from the formula
            """

            form = formula.replace('=', '')
            if 'TODAY()' in form:
                form = form.replace('TODAY()', 'datetime.date.today()')
            if '+' in form:
                parts = form.split('+')
                parts[1] = 'datetime.timedelta(days=' + parts[1] + ')'
                form = parts[0] + '+' + parts[1]
            elif '-' in form:
                parts = form.split('-')
                parts[1] = 'datetime.timedelta(days=' + parts[1] + ')'
                form = parts[0] + '-' + parts[1]
            return eval(form)

        if validate == 'length':
            if criteria == 'between':
                return Evaluator(validation, func=lambda self, x: self.validation['minimum'] <= len(x) <= self.validation['maximum'])
            else:
                return Evaluator(validation, func=lambda self, x: eval("len(x) " + self.validation['criteria'] + str(self.validation['value'])))
        elif validate == 'decimal':
            if criteria == 'between':
                return Evaluator(validation, func=lambda self, x: (isinstance(x, int) or isinstance(x, float)) and self.validation['minimum'] <= float(x) <= self.validation['maximum'])
            else:
                return Evaluator(validation, func=lambda self, x: (isinstance(x, int) or isinstance(x, float)) and eval("float(x) " + self.validation['criteria'] + "self.validation['value']"))
        elif validate == 'integer':
            if criteria == 'between':
                return Evaluator(validation, func=lambda self, x: isinstance(x, int) and self.validation['minimum'] <= int(x) <= self.validation['maximum'])
            else:
                return Evaluator(validation, func=lambda self, x: isinstance(x, int) and eval("int(x) " + self.validation['criteria'] + "int(self.validation['value'])"))
        elif validate == 'time':
            if criteria == 'between':
                if isinstance(validation['minimum'], float) or isinstance(validation['minimum'], int):
                    minimum = (datetime.datetime(1, 1, 1, 0, 0) +
                                datetime.timedelta(days=validation['minimum'])).time()
                    maximum = (datetime.datetime(1, 1, 1, 0, 0) +
                                datetime.timedelta(days=validation['maximum'])).time()
                else:
                    minimum = validation['minimum']
                    maximum = validation['maximum']
                ev = Evaluator(validation)
                ev.minimum = minimum
                ev.maximum = maximum
                ev.set_func(lambda self, x: self.minimum <= x <= self.maximum)
                return ev
            else:
                if isinstance(validation['value'], float) or isinstance(validation['value'], int):
                    limit = (datetime.datetime(1, 1, 1, 0, 0) +
                              datetime.timedelta(days=validation['value'])).time()
                else:
                    limit = validation['value']

                ev = Evaluator(validation)
                ev.limit = limit
                ev.set_func(lambda self, x: eval(
                    "x" + self.validation['criteria'] + "self.limit"))
                return ev
        elif validate == 'date':
            if criteria == 'between':
                minimum = validation['minimum']
                maximum = validation['maximum']
                if not(isinstance(minimum, datetime.date)):
                    # We now have a formula
                    minimum = _formula_to_date(minimum)
                if not(isinstance(maximum, datetime.date)):
                    # We now have a formula
                    maximum = _formula_to_date(maximum)
                ev = Evaluator(validation)
                ev.minimum = minimum
                ev.maximum = maximum
                ev.set_func(lambda self, x: self.minimum <= x <= self.maximum)
                # ev.set_func(lambda self,x: print(self.minimum , x , self.maximum))
                return ev

            else:
                limit = validation['value']
                if not(isinstance(limit, datetime.date)):
                    # We now have a formula
                    limit = _formula_to_date(limit)

                ev = Evaluator(validation)
                ev.limit = limit

                ev.set_func(lambda self, x: eval(
                    "x" + self.validation['criteria'] + "self.limit"))

                return ev

            raise NotImplementedError("No validator available for the object")

def clean(data):
    """
    Goes through the array and cleans up the data
    Fixes some numbers that have not been converted correctly
    Converts uuids to lower and makes sure seperator is '-' and not '+' '/'
    Parameters
    ---------
    data: Pandas dataframe of data to be cleaned

    Returns
    ---------
    cleaned_data: Pandas dataframe
        The cleaned data
    """

    try:
        data['id'] = data['id'].replace('/','-', regex=True)
    except:
        pass

    try:
        data['id'] = data['id'].replace('+','-', regex=True)
    except:
        pass

    cleaned_data = data.copy()
    pd.set_option('mode.chained_assignment', None) # PREVENTING COPY WARNING ORIGINATING FROM BELOW

    for col in data.columns:
        if col != 'id':
            for idx, row in data.iterrows():
                try:
                    num = format_num(row[col])
                    cleaned_data[col][idx] = num # COPY WARNING
                except ValueError:
                    continue

    return cleaned_data

def to_ranges_str(lis):
    """
    Conversion of a list for integers to a string containing ranges.
    For instance [1, 2, 3, 4] will be returned as the string [1 - 4]
    Parameters
    ---------
    lis: list of ints
        The list to be converted
    Returns
    ---------
    out: string
        The resulting string with ranges for sequences consisting of more than
        two steps. Enclosed in swuare ([]) brackets
    """

    out = '['+str(lis[0])
    if len(lis) == 2:
        out = out + ', ' + str(lis[1])
    elif len(lis) > 2:
        first = lis[0]
        prev = first
        ii = 1
        for l in lis[1:]:

            if l == prev+1:
                prev = l
                ii = ii+1
            else:
                # longer step
                if ii > 2:
                    out = out + ' - ' + str(prev)
                # else:
                    # out = out +', '+str(prev)
                prev = l
                first = l
                out = out + ', ' + str(first)
                ii = 0
        if ii > 2:
            out = out + ' - ' + str(prev)
        # else:
            # out = out +', '+str(prev)

    out = out + ']'
    return out

def check_value(value, checker):
    """
    Check the value with the checker.
    Does some additional checks in addition to the checks in checker
    Parameters
    ---------
    value: object
        The value to be checked
    checker: Checker
        The Checker to use
    Returns
    ---------
    bool : Boolean
        True, passed
        False, failed
    """

    if value == '' or is_nan(value) or (isinstance(value, float) and np.isnan(value)):
        return True
    if checker.validation['validate'] == 'length':
        for ID in ['id', 'parentID', 'measurementID','eventID', 'occurrenceID']:
            if ID in checker.name.lower():
                try:
                    uuid.UUID(value)
                except ValueError:
                    return False

    if checker.validation['validate'] == 'date':
        try:
            value = value.to_pydatetime().date()
        except:
            pass
        if type(value) == datetime.date(1, 1, 1).__class__:
            return checker.validator.evaluate(value)
    elif checker.validation['validate'] == 'time':
        value = value.to_pydatetime().time()
        return checker.validator.evaluate(value)
    elif checker.validation['validate'] == 'integer' or checker.validation['validate'] == 'decimal':
        try:
            num = format_num(value)
        except ValueError:
            num = value
        return checker.validator.evaluate(num)
    else:
        return checker.validator.evaluate(value)

def check_array(data, checker_list, registered_ids, required, new):
    """
    Checks the data according to the validators in the checker_list
    Returns True if the data is good, as well as an empty string
    Parameters
    ---------
    data : numpy ndarray of objects
        The data to be checked.
        The first row should contain the names of the fields as specified in fields.py
    checker_list : dict of Checker objects
        This is a list of the possible checkers made by make_valid_dict
    required: List of required columns
    registered_ids: List of UUIDS
        This is a list of UUIDS already registered in the metadata catalogue,so we can check for duplicates
    new: Boolean
        Whether the record(s) is being logged for the first time or not
        Influences whether we check whether id already registered
    Returns
    ---------
    good : Boolean
        A boolean specifying if the data passed the checks (True)
    errors: list of strings
        A string per error, describing where the error was found
        On the form: paramName: disp_name : row
    """
    good = True
    errors = []

    for req in required:
        if req not in data.columns:
            good = False
            errors.append(f'Required field "{req}" is missing')

    # INHERIT BEFORE CHECKER SO COLUMNS MUST BE THERE REGARDLESS OF WHETHER THERE IS A PARENTID
    unknown_columns = []
    for col in data.columns:
        if col not in checker_list.keys():
            unknown_columns.append(col)
            good = False
    if unknown_columns != []:
        errors.append(f'Field name not recognised: {unknown_columns}')


    if not(good):
        errors.append("Not doing any more tests until all required fields are present and all fields are recognised")
        return good, errors

    already_registered_ids = []
    duplicate_ids = []
    parent_child = []
    missing_parents = []

    for idx, row in data.iterrows():
        if row['id'] != '':
            if row['id'] in registered_ids and new == True:
                good = False
                already_registered_ids.append(idx)
            elif not data['id'].is_unique:
                duplicate_ids.append(idx)
                good = False
            elif 'parentID' in data.columns:
                if data['id'] == data['parentID']:
                    parent_child.append(idx)
                    good = False
        if 'parentID' in data.columns:
            if row['parentID'] != '' and row['parentID'] not in registered_ids or row['parentID'] not in data['id'].values:
                missing_parents.append(idx)

    if already_registered_ids != []:
        if len(data) > 1:
            errors.append(f'ID(s) already registered in the system, Rows: {already_registered_ids}')
        else:
            errors.append('ID already registered in the system')

    if duplicate_ids != []:
        if len(data) > 1:
            errors.append(f'ID(s) registered more than once in same upload, Rows: {duplicate_ids}')

    if parent_child != []:
        if len(data) > 1:
            errors.append(f'ID is same as Parent ID, Rows: {parent_child}')
        else:
            errors.append('ID and ParentID cannot be the same')

    if missing_parents != []:
        if len(data) > 1:
            errors.append(f'ParentID not registered, Rows {missing_parents}')
        else:
            errors.append('ParentID not registered in system')

    minmaxdepths = []
    minmaxelevations = []

    for col in data.columns:
        content_errors = []
        checker = checker_list[col]
        blanks = []

        for idx, row in data.iterrows():
            val = row[col]
            if not check_value(val, checker):

                content_errors.append(idx)

            if col in required:

                if val == '':
                    blanks.append(idx)

        if content_errors != []:
            if len(data) > 1:
                errors.append(checker.disp_name + ' ('+checker.name + ')'+", Rows: " +
                              to_ranges_str(content_errors) + ' Error: Content in wrong format')
            else:
                errors.append(f'Content in wrong format ({checker.disp_name})')

        if blanks != []:
            if len(data) > 1:
                errors.append(checker.disp_name + ' ('+checker.name + ')'+", Rows: " +
                              to_ranges_str(content_errors) + ' Error: Value missing (required)')
            else:
                errors.append(f'Required value missing ({checker.disp_name})')

        if col == 'minimumDepthInMeters' and 'minimumDepthInMeters' in data.columns:
            for idx, row in data.iterrows():
                mindepth = row[col]
                maxdepth = row['maximumDepthInMeters']
                if maxdepth != '' and mindepth != '':
                    if mindepth > float(maxdepth):
                        minmaxdepths.append(idx)

        if col == 'minimumElevationInMeters' and 'minimumElevationInMeters' in data.columns:
            for idx, row in data.iterrows():
                minelevation = row[col]
                maxelevation = row['maximumElevationInMeters']
                if maxelevation != '' and minelevation != '':
                    if minelevation > float(maxelevation):
                        minmaxelevations.append(idx)

    if minmaxdepths != []:
        if len(data) > 1:
            errors.append(f'Maximum depth must be greater than or equal to minimum depth, Rows: {minmaxdepths}')
        else:
            errors.append('Maximum depth must be greater than or equal to minimum depth.')

    if minmaxelevations != []:
        if len(data) > 1:
            errors.append(f'Maximum elevation must be greater than or equal to minimum depth, Rows: {minmaxdepths}')
        else:
            errors.append('Maximum elevation must be greater than or equal to minimum depth.')

    missingdepths = []

    for idx, row in data.iterrows():
        n = 0
        for col in ['minimumDepthInMeters', 'maximumDepthInMeters', 'minimumElevationInMeters', 'maximumElevationInMeters']:
            if col in data.columns:
                if row[col] == '':
                    n = n + 1
        if n == 4:
            missingdepths.append(idx)

    if missingdepths != []:
        if len(data) > 1:
            errors.append(f'Please include an elevation or depth (preferably both minimum and maximum, they can be the same), Rows: {missingdepths}')
        else:
            errors.append('Please include an elevation or depth (preferably both minimum and maximum, they can be the same)')

    '''
    Potential additional checks:
        1. Prevent people entering both elevation and depth.
        2. Reject activities logged with same date and time as another activity
    '''

    return good, errors

def run(data, required=[], DBNAME=False, METADATA_CATALOGUE=False, new=True):
    """
    Method for running the checker on the given input.
    If importing in another program, this should be called instead of the main
    function
    Can be used to return the data as well
    Parameters
    ---------
    data: Pandas dataframe
        Pandas dataframe of data to be checked.
        'other' hstore should be expanded into separate columns before input
    required: List
        List of required columns
        Default: Empty list []
    DBNAME: str
        Name of PSQL database that hosts the metadata catalogue
        and other tables where lists of values for certain fields are registered
        Default: False boolean
    METADATA_CATALOGUE: str
        Name of the metadata catalogue table within DBNAME
        Default: False boolean
    new: Boolean
        Whether the record(s) is being logged for the first time or not
        Influences whether we check whether id already registered

    Returns
    ---------
    good: Boolean
        The result.
        True: pass
        False: fail
    errors: string
        String specifying where the errors were found
    """

    checker_list = make_valid_dict(DBNAME)

    data = clean(data)

    if DBNAME != False and METADATA_CATALOGUE != False:
        df_metadata_catalogue = get_data(DBNAME, METADATA_CATALOGUE)
        registered_ids = df_metadata_catalogue['id'].values
    else:
        registered_ids = []

    # Check the data array
    good, errors = check_array(data, checker_list, registered_ids, required, new)

    return good, errors

# def checker(input_metadata, df_metadata_catalogue, DBNAME, ID):
#     '''
#     Checks data before they can be imported into the metadata catalogue
#
#     input_metadata: Dictionary of fields and values, for example from an html form.
#     df_metadata_catalogue: pandas dataframe of metadata catalogue
#     DBNAME: name of the PostgreSQL database
#     ID: ID of the sample being registered. Listed as 'addNew' if not assigned yet, e.g. for a new activity where the user wants the system to create the ID.
#     '''
#
#     # Append error messages to list.
#     # If the list contains at least one error message after the checker has run, the record should be rejected
#     errors = []
#
#     df_metadata_catalogue['timestamp'] = pd.to_datetime(df_metadata_catalogue['eventdate'].astype(str)+' '+df_metadata_catalogue['eventtime'].astype(str))
#     registered_event_timestamps= list(df_metadata_catalogue['timestamp'])
#
#     # key is the field name, val is the value provided by the user that needs checking
#     for key, val in input_metadata.items():
#
#         # IDs
#         ids = df_metadata_catalogue['id'].values
#
#         # If any of required fields are blank, error and state what is missing.
#         if key in ['eventDate', 'eventTime', 'stationName', 'decimalLatitude', 'decimalLongitude', 'pis', 'recordedBys', 'gearType']:
#             if val == '':
#                 errors.append(f'{key} is required. Please provide a value.')
#
#         if key == 'id':
#             if val != '':
#                 val = val.replace('+','-').replace('/','-')
#                 try:
#                     uuid.UUID(val)
#                 except:
#                     errors.append('Not a valid ID. Please use a UUID, e.g. 10621b76-94c0-4cf5-8aa9-64697205da7d')
#             elif val in ids:
#                 errors.append('ID already registered')
#
#         if key == 'parentID':
#             if val != '':
#                 val = val.replace('+','-').replace('/','-')
#                 try:
#                     uuid.UUID(val)
#                 except:
#                     errors.append('Not a valid parent ID. Please use a UUID, e.g. 10621b76-94c0-4cf5-8aa9-64697205da7d')
#             elif val not in ids:
#                 errors.append(f'Parent with the ID {val} has not been registered')
#
#         # Coordinates
#         if key in ['decimalLatitude', 'middleDecimalLatitude', 'endDecimalLongitude']:
#             if val != '':
#                 if -90 <= float(val) <= 90:
#                     continue
#                 else:
#                     errors.append('Latitude must be between -90 and 90 degrees')
#
#         if key in ['decimalLongitude', 'middleDecimalLongitude', 'endDecimalLongitude']:
#             if val != '':
#                 if -180 <= float(val) <= 180:
#                     continue
#                 else:
#                     errors.append('Latitude must be between -180 and 180 degrees')
#
#         # Depths and elevations
#         if key in ['minimumDepthInMeters', 'maximumDepthInMeters', 'minimumElevationInMeters', 'maximumElevationInMeters']:
#             if val != '':
#                 val = float(val)
#                 if 0 <= val <= 30000:
#                     pass
#                 elif 30000 < float(val):
#                     errors.append(f'{key} must be less than or equal to 30000')
#                 else:
#                     errors.append(f'{key} must be a number greater than 0')
#
#                 if key == 'minimumDepthInMeters':
#                     maxdepth = input_metadata['maximumDepthInMeters']
#                     # Maybe sometimes only one depth (min or max) is known?
#                     # if maxdepth == '':
#                     #     errors.append('You have entered a minimum depth. Please also enter a maximum depth. They can be the same if a single depth was sampled.')
#                     if maxdepth != '':
#                         if val > float(maxdepth):
#                             errors.append('Maximum depth must be greater than or equal to minimum depth')
#
#                 if key == 'minimumElevationInMeters':
#                     maxelevation = input_metadata['maximumElevationInMeters']
#                     if maxelevation != '':
#                         if val > float(maxelevation):
#                             errors.append('Maximum elevation must be greater than minimum elevation')
#
#         # Dates and times
#         if key == 'eventDate':
#             if val != '' and input_metadata['eventTime'] != '':
#                 timestamp = dt.strptime(val + input_metadata['eventTime'], "%Y-%m-%d%H:%M:%S")
#                 if dt.utcnow() < timestamp:
#                     errors.append('Time and date must be before current UTC time')
#
#                 # Not performing this check on activities when the metadata is being edited because obviously it is already registered in the system.
#                 if 'parentID' in input_metadata.keys():
#                     if input_metadata['parentID'] == '' and timestamp in registered_event_timestamps and ID == 'addNew':
#                         errors.append('Another activity has already been registered at the same date and time.')
#                 else:
#                     if timestamp in registered_event_timestamps and ID == 'addNew':
#                         errors.append('Another activity has already been registered at the same date and time.')
#
#         if key == 'middleDate': # What is they provide date and not time or vice versa?
#             if val != '':
#                 timestamp_mid = dt.strptime(val + input_metadata['middleTime'], "%Y-%m-%d%H:%M:%S")
#                 if dt.utcnow() < timestamp_mid:
#                     errors.append('Time and date must be before current UTC time')
#                 timestamp_start = dt.strptime(input_metadata['eventDate'] + input_metadata['eventTime'], "%Y-%m-%d%H:%M:%S")
#                 if timestamp_start > timestamp_mid:
#                     errors.append('Mid time must be after the start time')
#
#
#         if key == 'endDate': # What is they provide date and not time or vice versa?
#             if val != '':
#                 timestamp_end = dt.strptime(val + input_metadata['endTime'], "%Y-%m-%d%H:%M:%S")
#                 if dt.utcnow() < timestamp_end:
#                     errors.append('Time and date must be before current UTC time')
#                 timestamp_start = dt.strptime(input_metadata['eventDate'] + input_metadata['eventTime'], "%Y-%m-%d%H:%M:%S")
#                 if timestamp_start > timestamp_end:
#                     errors.append('End time must be after the start time')
#                 try:
#                     timestamp_mid = dt.strptime(input_metadata['middleDate'] + input_metadata['middleTime'], "%Y-%m-%d%H:%M:%S")
#                     if timestamp_mid > timestamp_end:
#                         errors.append('End time must be after the middle time')
#                 except:
#                     pass
#
#         # Personnel
#         if key in ['pis', 'recordedBys']:
#
#             df_personnel = get_data(DBNAME, 'personnel')
#             df_personnel.sort_values(by='last_name', inplace=True)
#             df_personnel['personnel'] = df_personnel['first_name'] + ' ' + df_personnel['last_name'] + ' (' + df_personnel['email'] + ')'
#             personnel = list(df_personnel['personnel'])
#             for person in val:
#                 if person not in personnel:
#                     if person != '':
#                         errors.append(f'{person} is not registered in the system. You may need to register a new person first.')
#
#         # Values from lists
#         if key == 'gearType':
#
#             df_gears = get_data(DBNAME, 'gear_types')
#             df_gears.sort_values(by='geartype', inplace=True)
#             gearTypes = list(df_gears['geartype'])
#
#             if val not in gearTypes:
#                 errors.append('Please select a gear type registered in the system. You may need to register a new gear type first.')
#
#         if key == 'sampleType':
#
#             if val != '':
#                 df_samples = get_data(DBNAME, 'sample_types')
#                 df_samples.sort_values(by='sampletype', inplace=True)
#                 sampleTypes = list(df_samples['sampletype'])
#
#                 if val not in sampleTypes:
#                     errors.append('Please select a sample type registered in the system. You may need to register a new sample type first.')
#
#         if key == 'intendedMethod':
#
#             if val != '':
#                 df_intendmethods = get_data(DBNAME, 'intended_methods')
#                 df_intendmethods.sort_values(by='intendedmethod', inplace=True)
#                 intendedMethods = list(df_intendedmethods['intendedmethod'])
#
#                 if val not in intendedMethods:
#                     errors.append('Please select an intended method registered in the system. You may need to register a new intended method first.')
#
#         if key == 'stationName':
#
#             df_stations = get_data(DBNAME, 'stations')
#             df_stations.sort_values(by='stationname', inplace=True)
#             stationNames = list(df_stations['stationname'])
#
#             if val not in stationNames:
#                 errors.append('Please select a station name from the drop-down list. You may need to register a new station name first.')
#
#     n = 0
#     for key in ['minimumDepthInMeters', 'maximumDepthInMeters', 'minimumElevationInMeters', 'maximumElevationInMeters']:
#         if input_metadata[key] == '':
#             n = n + 1
#     if n == 4:
#         errors.append('Please include an elevation or depth (preferably both minimum and maximum, they can be the same)')
#
#     elif input_metadata['minimumDepthInMeters'] != '' or input_metadata['maximumDepthInMeters'] != '':
#         if input_metadata['minimumElevationInMeters'] != '' or input_metadata['maximumElevationInMeters'] != '':
#             errors.append('It is not possible to enter an elevation and a depth.')
#
#     return errors
