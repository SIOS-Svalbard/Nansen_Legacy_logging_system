#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 15:27:00 2022

@author: lukem
"""

'''
 -- This file is for defining the possible metadata fields.
Each field is defined as a dictionary which should contain:
    name :       short name of field
    disp_name :  The displayed name of the field
    format:      uuid, int, text, time, date, double precision, boolean
    description: Description of the field
    grouping:    Categorising the fields so they can be grouped on the user interface, making it easier for the user to find what they are looking for.
                 groups: [
                 'Dataset Details',
                 'Cruise Details',
                 ]
    valid :      dict
                 a dictionary with definitions of the validation for the cell, as
                 per keywords used in Xlsxwriter

Optional fields are:
    width : int
            the width of the cell
    long_list: Boolean
            If the list wil exceed the Excel number of fields set this as true
    inherit : Boolean
             Is this a field that can be inherited by children?
             If it is not present its default is False
    units : str
            The measurement unit of the variable, using the standard in CF
           Examples: 'm', 'm s-1', '
    eml_name : str
            The field name in the Ecological Metadata Language conventions,
            recommended for use in Darwin Core Archives
    acdd_name : str
             The field name in the ACDD conventions, recommended for use in NetCDF files
             https://wiki.esipfed.org/Attribute_Convention_for_Data_Discovery_1-3
    cell_format :  dict
                   a dictionary with definitions of the format for the cell, as
                   per keywords in Xlsxwriter
'''

import datetime as dt

metadata_fields = [

    # ==============================================================================
    # Terms required by arctic data centre for NetCDF/CF files
    # https://adc.met.no/node/4
    # ==============================================================================
    {'name': 'title',
                'disp_name': 'Title',
                'acdd_name': 'title',
                'acdd_description': 'A short phrase or sentence describing the dataset. In many discovery systems, the title will be displayed in the results list from a search, and therefore should be human readable and reasonable to display in a list of such names. This attribute is also recommended by the NetCDF Users Guide and the CF conventions.',
                'eml_name': 'title',
                'eml_description': '',
                'inherit': True,
                'format': 'int',
                'grouping': 'Dataset Details',
                'valid': {
                    'validate': 'any'}
                },


    # ==============================================================================
    # Cruise Details - all in metadata hstore
    # ==============================================================================
    {'name': 'cruiseNumber',
                'disp_name': 'Cruise number',
                'description': 'A number that can be used to uniquely identify each cruise',
                'inherit': True,
                'format': 'int',
                'grouping': 'Cruise Details',
                'valid': {
                    'validate': 'any'}
                },
    {'name': 'cruiseName',
                'disp_name': 'Cruise name',
                'description': 'Full name of the cruise',
                'inherit': True,
                'format': 'text',
                'grouping': 'Cruise Details',
                'valid': {
                    'validate': 'any'}
                },
    {'name': 'projectName',
                'disp_name': 'Project name',
                'description': 'Full name of the project',
                'inherit': True,
                'format': 'text',
                'grouping': 'Cruise Details',
                'valid': {
                    'validate': 'any'}
                },
    {'name': 'vesselName',
                'disp_name': 'Vessel name',
                'description': 'Full name of the vessel',
                'inherit': True,
                'format': 'text',
                'grouping': 'Cruise Details',
                'valid': {
                    'validate': 'any'}
                },
    ]
