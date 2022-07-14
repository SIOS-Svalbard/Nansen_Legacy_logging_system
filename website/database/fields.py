#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 11 08:48:12 2022

@author: lukem
"""

'''
 -- This file is for defining the possible fields.
Each field is defined as a dictionary which should contain:
    name :       short name of field
    disp_name :  The displayed name of the field
    format:      uuid, int, text, time, date, double precision, boolean
    description: Description of the field
    hstore:      Whether the field should be contained in an hstore column or serve as a standalone column.
                 The hstore columns are:
                    metadata (metadata describing the entire dataset, e.g. title, abstract, PI details)
                    other (any other column that is not provided for all or most events, therefore doesn't warrant it's own column)
                 Therefore, the following values are acceptable:
                    metadata
                    other
                    False
                 DIFFERENT HSTORES FOR DIFFERENT GROUPS?
Optional fields are:
    sampleTypes: list
            List of sample types that the term is a recommended column for. Can be 'ALL' or taken from sample types table.
    intendedMethods: list
            List of intended methods that the term is a recommended column for. Can be 'ALL' or taken from intended methods table.
    width : int
            the width of the cell
    long_list: Boolean
            If the list wil exceed the Excel number of fields set this as true
    dwcid : str
            The Darwin core identifier (an url), if this is used the rest of the names should
            follow the Darwin core
    units : str
            The measurement unit of the variable, using the standard in CF
           Examples: 'm', 'm s-1', '
    cf_name : str
             The variable name in the CF standard
    inherit : Boolean
             Is this a variable that can be inherited by children?
             If it is not present its default is False
    inherit_weak : Boolean
             Only used if inherit is true. If set to True values already
             entered in the children will be kept.
             This is useful for instance in the case of multinets where the
             individual nets have different max and min depths.
             If it is not present its default is False
    valid : dict
            a dictionary with definitions of the validation for the cell, as
            per keywords used in Xlsxwriter
    cell_format :  dict
                   a dictionary with definitions of the format for the cell, as
                   per keywords in Xlsxwriter
'''

import datetime as dt


fields = [
    # ==============================================================================
    # ID fields
    # ==============================================================================

    {'name': 'id',
           'disp_name': 'ID',
           'description': '''A 36 character long universally unique ID (UUID) including 4 '-'.
Could be read in with a code reader.''',
           'width': 38,
           'format': 'uuid',
           'hstore': False,
           'valid': {
               'validate': 'length',
               'criteria': '==',
               'value': 36,
               'input_title': 'ID',
               'input_message': '''Should be a 36 character long universally unique ID (UUID) including 4 '-'.
Could be read in with a code reader.''',
               'error_title': 'Error',
               'error_message': "Needs to be a 36 characters long universally unique ID (UUID) including 4 '- '"
           }
           },
    {'name': 'parentID',
                 'disp_name': 'Parent ID',
                 'description': '''ID of the sample this subsample was taken from.
Should be a 36 characters long universally unique ID (UUID) including 4 '-'
Could be read in with a code reader.''',
                 'width': 38,
                 'format': 'uuid',
                 'hstore': False,
                 'valid': {
                     'validate': 'length',
                     'criteria': '==',
                     'value': 36,
                     'input_title': 'Parent ID',
                     'input_message': '''ID of the sample this subsample was taken from.
Should be a 36 characters long universally unique ID (UUID) including 4 '-'
Could be read in with a code reader.''',
                     'error_title': 'Error',
                     'error_message': "Needs to be a 36 characters long universally unique ID (UUID) including 4 '- '"
                 }
                 },
    {'name': 'catalogNumber',
                 'disp_name': 'Catalogue Number',
                 'description': '''Your own optional ID for each record, preferably unique. Note that each sample is also assigned its own UUID in the "ID" field by the system.''',
                 'width': 38,
                 'format': 'text',
                 'hstore': False,
                 'valid': {
                     'validate': 'length',
                     'criteria': '==',
                     'value': 36,
                     'input_title': 'Parent ID',
                     'input_message': '''Your own optional ID for each record, preferably unique. Note that each sample is also assigned its own UUID in the "ID" field by the system.''',
                     'error_title': 'Error',
                     'error_message': "Needs to be a 36 characters long universally unique ID (UUID) including 4 '- '"
                 }
                 },
    {'name': 'bottleNumber',
                'disp_name': 'Bottle Number',
                'description': '''The bottle number
Could be for instance the niskin bottle number.
Positive integer''',
                'inherit': True,
                'format': 'int',
                'hstore': False,
                'valid': {
                    'validate': 'integer',
                    'criteria': '>',
                    'value': 0,
                    'input_title': 'Bottle Number',
                    'input_message': '''The bottle number
Could be for instance the niskin bottle number.
Positive integer''',
                    'error_title': 'Error',
                    'error_message': 'Integer > 0'
                }
                },
    {'name': 'recordNumber',
                'disp_name': 'Record Number',
                'description': '''This is an additional number used to identify the sample.
This is in addition to the ID''',
                'format': 'int',
                'hstore': 'other',
                'dwcid': 'http://rs.tdwg.org/dwc/terms/recordNumber',
                'valid': {
                    'validate': 'any',
                    'input_title': 'Recorded Number',
                    'input_message': '''This is an additional number used to identify the sample.
This is in addition to the ID'''
                }
                },

    # ==============================================================================
    # Cruise details
    # ==============================================================================
    {'name': 'cruiseNumber',
                'disp_name': 'Cruise number',
                'description': 'A number that can be used to uniquely identify each cruise',
                'inherit': True,
                'format': 'int',
                'hstore': False,
                'valid': {
                    'validate': 'any',
                    'input_title': 'Cruise Number',
                    'input_message': '''This is the same for one cruise''',
                    'error_title': 'Error',
                    'error_message': 'Not a valid cruise number '
                }
                },
    {'name': 'cruiseName',
                'disp_name': 'Cruise name',
                'description': 'Full name of the cruise',
                'inherit': True,
                'format': 'text',
                'hstore': False
                },
    {'name': 'projectName',
                'disp_name': 'Project name',
                'description': 'Full name of the project',
                'inherit': True,
                'format': 'text',
                'hstore': False
                },
    {'name': 'vesselName',
                'disp_name': 'Vessel name',
                'description': 'Full name of the vessel',
                'inherit': True,
                'format': 'text',
                'hstore': False
                },

    # ==============================================================================
    # Station details
    # ==============================================================================
    {'name': 'statID',
          'disp_name': 'Local Station ID',
          'description': 'This ID is a running series (per gear) for each samling event and is found in the cruise logger.',
          'inherit': True,
          'width': 13,
          'format': 'int',
          'hstore': False,
          'valid': {
              'validate': 'any',
              'input_title': 'Local Station ID',
              'input_message': '''This ID is a running series (per gear) for each samling event and is found in the cruise logger.
'''
          }
          },
    # ADD TABLE FOR DROPDOWN? RETHINK HOW STATION NAMES WILL BE HANDLED IN THIS SYSTEM. USEFUL FOR SCIENTISTS BUT MUST BE MANAGED MORE CONSISTENTLY THAN IN AEN
    # SUGGESTED STATION NAMES BASED - THIS ACTIVITY OCCURRED xx METERS FROM THIS STATION.
    {'name': 'stationName',
               'disp_name': 'Station Name',
               'description': 'The full name of the station. e.g. P1 (NLEG01)',
               'inherit': True,
               'width': 13,
               'format': 'text',
               'hstore': False,
               'valid': {
                   'validate': 'any',
                   'input_title': 'Station Name',
                   'input_message': '''The full name of the station. e.g. P1 (NLEG01)'''
               }
               },

    # ==============================================================================
    # Timestamps
    # ==============================================================================
    {'name': 'eventDate',
             'disp_name': 'Event Date',
             'description': 'Timestamp that the data were collected at. Should be in ISO8601 format, in UTC time, e.g. 2022-04-10T09:46:24Z',
             'inherit': True,
             'format': 'date',
             'hstore': False,
             'width': 12,
             'dwcid': 'http://rs.tdwg.org/dwc/terms/eventDate',
             'valid': {
                 'validate': 'date',
                 'criteria': 'between',
                 'minimum': dt.datetime(2000, 1, 1),
                 'maximum': '=TODAY()+2',
                 'input_title': 'Event Date',
                 'input_message': '''Timestamp that the data were collected at. Should be in ISO8601 format, in UTC time, e.g. 2022-04-10''',
                 'error_title': 'Error',
                 'error_message': 'Not a valid date [2000-01-01, today + 2]'
             },
             'cell_format': {
                 'num_format': 'yyyy-mm-dd'
             }
             },
    {'name': 'eventTime',
             'disp_name': 'Time (UTC)',
             'description': 'Timestamp that the data were collected at. Should be in ISO8601 format, in UTC time, e.g. 09:46:24Z',
             'inherit': True,
             'format': 'time',
             'hstore': False,
             'width': 13,
             'dwcid': 'http://rs.tdwg.org/dwc/terms/eventTime',
             'valid': {
                 'validate': 'time',
                 'criteria': 'between',
                 'minimum': 0,  # Time in decimal days
                 'maximum': 0.9999999,  # Time in decimal days
                 'input_title': 'Event Time (UTC)',
                 'input_message': '''
The time in UTC
Format is HH:MM
If MM > 59, HH will be HH + 1 ''',
                 'error_title': 'Error',
                 'error_message': 'Not a valid time'
             },
             'cell_format': {
                 'num_format': 'hh:mm'
             }
             },
    {'name': 'middleDate',
             'disp_name': 'Middle Date',
             'description': '''Middle date for event, for instance for noting the deepest point of a trawl or net haul.
Should be in ISO8601 format, in UTC time, e.g. 2022-04-10''',
             'inherit': True,
             'format': 'date',
             'hstore': 'other',
             'width': 12,
             'valid': {
                 'validate': 'date',
                 'criteria': 'between',
                 'minimum': dt.datetime(2000, 1, 1),
                 'maximum': '=TODAY()+2',
                 'input_title': 'Start Date',
                 'input_message': '''Middle date for event, for instance for noting the deepest point of a trawl or net haul.
Should be in ISO8601 format, in UTC time, e.g. 2022-04-10T09:46:24Z''',
                 'error_title': 'Error',
                 'error_message': 'Not a valid date [2000-01-01, today + 2]'
             },
             'cell_format': {
                 'num_format': 'yyyy-mm-dd'
             }
             },
    {'name': 'middleTime',
             'disp_name': 'Middle Time',
             'description': '''Middle time for event, for instance for noting the deepest point of a trawl or net haul.
Should be in ISO8601 format, in UTC time, e.g. 09:46:24Z''',
             'inherit': True,
             'format': 'time',
             'hstore': 'other',
             'width': 12,
             'valid': {
                 'validate': 'date',
                 'criteria': 'between',
                 'minimum': 0,  # Time in decimal days
                 'maximum': 0.9999999,  # Time in decimal days
                 'input_title': 'Start Date',
                 'input_message': '''Middle time for event, for instance for noting the deepest point of a trawl or net haul.
Should be in ISO8601 format, in UTC time, e.g. 09:46:24Z''',
                 'error_title': 'Error',
                 'error_message': 'Not a valid date [2000-01-01, today + 2]'
             },
             'cell_format': {
                 'num_format': 'yyyy-mm-dd'
             }
             },
    {'name': 'endDate',
             'disp_name': 'End Date',
             'description': '''Date of the end of the collection event period,
Should be in ISO8601 format, in UTC time, e.g. 2022-04-10''',
             'inherit': True,
             'format': 'date',
             'hstore': False,
             'width': 12,
             'valid': {
                 'validate': 'date',
                 'criteria': 'between',
                 'minimum': dt.datetime(2000, 1, 1),
                 'maximum': '=TODAY()+2',
                 'input_title': 'End Date',
                 'input_message': '''Date of the end of the collection event period, in UTC time, e.g. 2022-04-10''',
                 'error_title': 'Error',
                 'error_message': 'Not a valid date [2000-01-01, today + 2]'
             },
             'cell_format': {
                 'num_format': 'yyyy-mm-dd'
             }
             },
        {'name': 'endTime',
                 'disp_name': 'End Time',
                 'description': '''Time of the end of the collection event period,
    Should be in ISO8601 format, in UTC time, e.g. 09:46:24Z''',
                 'inherit': True,
                 'format': 'time',
                 'hstore': False,
                 'width': 13,
                 'dwcid': 'http://rs.tdwg.org/dwc/terms/eventTime',
                 'valid': {
                     'validate': 'time',
                     'criteria': 'between',
                     'minimum': 0,  # Time in decimal days
                     'maximum': 0.9999999,  # Time in decimal days
                     'input_title': 'End Time (UTC)',
                     'input_message': '''
    The time in UTC
    Format is HH:MM
    If MM > 59, HH will be HH + 1 ''',
                     'error_title': 'Error',
                     'error_message': 'Not a valid time'
                 },
                 'cell_format': {
                     'num_format': 'hh:mm'
                 }
                 },

    # ==============================================================================
    # Coordinates
    # ==============================================================================
    {'name': 'decimalLatitude',
                   'disp_name': 'Decimal Latitude',
                   'description': '''Latitude in decimal degrees.
Northern hemisphere is positive.
Example: 78.1500''',
                   'inherit': True,
                   'format': 'double precision',
                   'hstore': False,
                   'width': 10,
                   'units': 'degrees_north',
                   'dwcid': 'http://rs.tdwg.org/dwc/terms/decimalLatitude',
                   'valid': {
                       'validate': 'decimal',
                       'criteria': 'between',
                       'minimum': -90,
                       'maximum': 90,
                       'input_title': 'Decimal Latitude',
                       'input_message': '''Latitude in decimal degrees.
Northern hemisphere is positive.
Example: 78.1500''',
                       'error_title': 'Error',
                       'error_message': 'Not in range [-90, 90]'
                   },
                   'cell_format': {
                       'num_format': '0.0000'
                   }
                   },
    {'name': 'decimalLongitude',
                    'disp_name': 'Decimal Longitude',
                    'description': '''Longitude in decimal degrees.
East of Greenwich (0) is positive.
Example: 15.0012''',
                    'inherit': True,
                    'format': 'double precision',
                    'hstore': False,
                    'width': 11,
                    'units': 'degree_east',
                    'dwcid': 'http://rs.tdwg.org/dwc/terms/decimalLongitude',
                    'valid': {
                        'validate': 'decimal',
                        'criteria': 'between',
                        'minimum': -180,
                        'maximum': 180,
                        'input_title': 'Decimal Longitude',
                        'input_message': '''Longitude in decimal degrees.
East of Greenwich (0) is positive.
Example: 15.0012''',
                        'error_title': 'Error',
                        'error_message': 'Not in range [-180, 180]'
                    },
                    'cell_format': {
                        'num_format': '0.0000'
                    }
                    },
    {'name': 'endDecimalLatitude',
                      'disp_name': 'End Decimal Latitude',
                      'description': '''Latitude in decimal degrees at the end of the sampling period.
   Northern hemisphere is positive.
   Example: 78.1500''',
                      'inherit': True,
                      'format': 'double precision',
                      'hstore': False,
                      'units': 'degrees_north',
                      'valid': {
                          'validate': 'decimal',
                          'criteria': 'between',
                          'minimum': -90,
                          'maximum': 90,
                          'input_title': 'End Decimal Latitude',
                          'input_message': '''Latitude in decimal degrees.
This is for use with for instance trawls and nets.
Northern hemisphere is positive.
Example: 78.1500''',
                          'error_title': 'Error',
                          'error_message': 'Not in range [-90, 90]'
                      },
                      'cell_format': {
                          'num_format': '0.0000'
                      }
                      },
    {'name': 'endDecimalLongitude',
                       'disp_name': 'End Decimal Longitude',
                       'description': '''Longitude in decimal degrees at the end of the sampling period.
   East of Greenwich (0) is positive.
   Example: 15.0012''',
                       'inherit': True,
                       'format': 'double precision',
                       'hstore': False,
                       'units': 'degree_east',
                       'valid': {
                           'validate': 'decimal',
                           'criteria': 'between',
                           'minimum': -180,
                           'maximum': 180,
                           'input_title': 'End Decimal Longitude',
                           'input_message': '''Longitude in decimal degrees.
This is for use with for instance trawls and nets.
East of Greenwich (0) is positive.
Example: 15.0012''',
                           'error_title': 'Error',
                           'error_message': 'Not in range [-180, 180]'
                       },
                       'cell_format': {
                           'num_format': '0.0000'
                       }
                       },
    {'name': 'middleDecimalLatitude',
                         'disp_name': 'Middle Decimal Latitude',
                         'description': '''Latitude in decimal degrees.
This is for use with for instance trawls and nets and denotes the depest point.
Northern hemisphere is positive.
Example: 78.1500''',
                         'inherit': True,
                         'format': 'double precision',
                         'hstore': 'other',
                         'units': 'degrees_north',
                         'valid': {
                             'validate': 'decimal',
                             'criteria': 'between',
                             'minimum': -90,
                             'maximum': 90,
                             'input_title': 'Middle Decimal Latitude',
                             'input_message': '''Latitude in decimal degrees.
This is for use with for instance trawls and nets and denotes the depest point.
Northern hemisphere is positive.
Example: 78.1500''',
                             'error_title': 'Error',
                             'error_message': 'Not in range [-90, 90]'
                         },
                         'cell_format': {
                             'num_format': '0.0000'
                         }
                         },
    {'name': 'middleDecimalLongitude',
                          'disp_name': 'Middle Decimal Longitude',
                          'description': '''Longitude in decimal degrees.
This is for use with for instance trawls and nets and denotes the depest point.
East of Greenwich (0) is positive.
Example: 15.0012''',
                          'inherit': True,
                          'format': 'double precision',
                          'hstore': 'other',
                          'units': 'degree_east',
                          'valid': {
                              'validate': 'decimal',
                              'criteria': 'between',
                              'minimum': -180,
                              'maximum': 180,
                              'input_title': 'Middle Decimal Longitude',
                              'input_message': '''Longitude in decimal degrees.
This is for use with for instance trawls and nets and denotes the depest point.
East of Greenwich (0) is positive.
Example: 15.0012''',
                              'error_title': 'Error',
                              'error_message': 'Not in range [-180, 180]'
                          },
                          'cell_format': {
                              'num_format': '0.0000'
                          }
                          },

    # ==============================================================================
    # Ship
    # ==============================================================================
    {'name': 'shipSpeedInMetersPerSecond',
                              'disp_name': 'Ship Speed (m/s)',
                              'description': '''The speed of the ship in meters per second.
Decimal number >=0.''',
                              'inherit': True,
                              'format': 'double precision',
                              'hstore': 'other',
                              'units': 'm/s',
                              'valid': {
                                  'validate': 'decimal',
                                  'criteria': '>=',
                                  'value': 0,
                                  'input_title': 'Ship Speed (m/s)',
                                  'input_message': '''The speed of the ship in meters per second.
Decimal number >=0.''',
                                  'error_title': 'Error',
                                  'error_message': 'Float >= 0'
                              }
                              },

    # ==============================================================================
    # Depths & Altitudes
    # ==============================================================================
    {'name': 'bottomDepthInMeters',
                       'disp_name': 'Bottom Depth (m)',
                       'description': '''Sea floor depth below sea surface.
Bathymetric depth at measurement site.
0 is the surface.''',
                       'inherit': True,
                       'format': 'double precision',
                       'hstore': False,
                       'units': 'm',
                       'cf_name': 'sea_floor_depth_below_sea_surface',
                       'valid': {
                           'validate': 'decimal',
                           'criteria': '>=',
                           'value': 0,
                           'input_title': 'Bottom Depth (m)',
                           'input_message': '''Sea floor depth below sea surface.
Bathymetric depth at measurement site.
0 is the surface.''',
                           'error_title': 'Error',
                           'error_message': 'Float >= 0'
                       }
                       },
    {'name': 'maximumDepthInMeters',
                        'disp_name': 'Maximum depth(m)',
                        'description': '''The maximum depth sampled in meters.
0 m is the surface.
Positive numbers for increasing depth.''',
                        'inherit': True,
                        'inherit_weak': True,
                        'format': 'double precision',
                        'hstore': False,
                        'units': 'm',
                        'dwcid': 'http://rs.tdwg.org/dwc/terms/maximumDepthInMeters',
                        'valid': {
                            'validate': 'decimal',
                            'criteria': 'between',
                            'minimum': 0,
                            'maximum': 9999,
                            'input_title': 'Maximum depth in (m)',
                            'input_message': '''The maximum depth sampled in meters.
0 m is the surface.
Positive numbers for increasing depth.''',
                            'error_title': 'Error',
                            'error_message': 'Float[0, 9999]'
                        }
                        },
    {'name': 'minimumDepthInMeters',
                        'disp_name': 'Minimum depth (m)',
                        'description': '''The minimum depth sampled in meters.
0 m is the surface.
Positive numbers for increasing depth.''',
                        'inherit': True,
                        'inherit_weak': True,
                        'format': 'double precision',
                        'hstore': False,
                        'width': 22,
                        'units': 'm',
                        'dwcid': 'http://rs.tdwg.org/dwc/terms/minimumDepthInMeters',
                        'valid': {
                            'validate': 'decimal',
                            'criteria': 'between',
                            'minimum': 0,
                            'maximum': 9999,
                            # 'criteria': '<',
                            # 'value': '=INDIRECT(ADDRESS(ROW(),COLUMN()-1))',
                            'input_title': 'Minimum depth in (m)',
                            'input_message': '''The minimum depth sampled in meters.
0 m is the surface.
Positive numbers for increasing depth.''',
                            'error_title': 'Error',
                            'error_message': 'Decimal [0, 9999]'
                        }
                        },
    {'name': 'maximumElevationInMeters',
                            'disp_name': 'Maximum elevation(m)',
                            'description': '''The maximum elevation sampled in meters.
0 m is the surface.
Positive numbers for increasing elevation.''',
                            'inherit': True,
                            'inherit_weak': True,
                            'format': 'double precision',
                            'hstore': False,
                            'units': 'm',
                            'dwcid': 'http://rs.tdwg.org/dwc/terms/maximumElevationInMeters',
                            'valid': {
                                'validate': 'decimal',
                                'criteria': '>=',
                                'value': 0,
                                'input_title': 'Maximum elevation in (m)',
                                'input_message': '''The maximum elevation sampled in meters.
0 m is the surface.
Positive numbers for increasing elevation.''',
                                'error_title': 'Error',
                                'error_message': 'Float >=0'
                            }
                            },
    {'name': 'minimumElevationInMeters',
                            'disp_name': 'Minimum elevation(m)',
                            'description': '''The minimum elevation sampled in meters.
0 m is the surface.
Positive numbers for increasing elevation.''',
                            'inherit': True,
                            'inherit_weak': True,
                            'format': 'double precision',
                            'hstore': False,
                            'units': 'm',
                            'dwcid': 'http://rs.tdwg.org/dwc/terms/minimumElevationInMeters',
                            'valid': {
                                'validate': 'decimal',
                                'criteria': '>=',
                                'value': 0,
                                'input_title': 'Minimum elevation in (m)',
                                'input_message': '''The minimum elevation sampled in meters.
    0 m is the surface.
    Positive numbers for increasing elevation.''',
                                'error_title': 'Error',
                                'error_message': 'Float >=0'
                            }
                            },

    # ==============================================================================
    # Paleo
    # ==============================================================================
    {'name': 'sedimentCoreLengthInMeters',
                              'disp_name': 'Sediment Core Length (m)',
                              'description': 'The total sediment core length decimal in meters.',
                              'units': 'm',
                              'format': 'double precision',
                              'hstore': 'other',
                              'valid': {
                                  'validate': 'decimal',
                                  'criteria': '>=',
                                  'value': 0,
                                  'input_title': 'Sediment Core Length (m)',
                                  'input_message': '''The total sediment core length decimal in meters.''',
                                  'error_title': 'Error',
                                  'error_message': 'Float >= 0'
                              }
                              },
    {'name': 'sedimentCoreMaximumDepthInCentiMeters',
                                         'disp_name': 'Sediment Core Maximum Depth (cm)',
                                         'description': '''The sediment core maximum depth in centimeters.
This is measured from the top of the core.
Maximum for multicores is 60 cm
Maximum for gravity and piston cores is 3 000 cm.''',
                                         'units': 'cm',
                                         'format': 'double precision',
                                         'hstore': 'other',
                                         'valid': {
                                             'validate': 'decimal',
                                             'criteria': 'between',
                                             'minimum': 0,
                                             'maximum': 3000,
                                             'input_title': 'Sediment Core Maximum Depth (m)',
                                             'input_message': '''The sediment core maximum depth in centimeters.
This is measured from the top of the core.
Maximum for multicores is 60 cm
Maximum for gravity and piston cores is 3 000 cm.''',
                                             'error_title': 'Error',
                                             'error_message': 'Float[0, 3 000]'
                                         }
                                         },
    {'name': 'sedimentCoreMinimumDepthInCentiMeters',
                                         'disp_name': 'Sediment Core Minimum Depth (cm)',
                                         'description': '''The sediment core minimum depth in centimeters.
This is measured from the top of the core.''',
                                         'units': 'cm',
                                         'format': 'double precision',
                                         'hstore': 'other',
                                         'valid': {
                                             'validate': 'decimal',
                                             'criteria': 'between',
                                             'minimum': 0,
                                             'maximum': 3000,
                                             'input_title': 'Sediment Core Minimum Depth (m)',
                                             'input_message': '''The sediment core minimum depth in centimeters.
This is measured from the top of the core.''',
                                             'error_title': 'Error',
                                             'error_message': 'Float[0, 3 000]'
                                         }
                                         },

    # ==============================================================================
    # Strings
    # ==============================================================================
    {'name': 'colour',
            'disp_name': 'Colour',
            'description': 'Colour of the sample or specimen',
            'format': 'text',
            'hstore': 'other',
            'valid': {
                'validate': 'any',
                'input_title': 'Colour',
                'input_message': 'Colour'
            }
            },
    {'name': 'smell',
            'disp_name': 'Smell',
            'description': 'A descriptive word or term for the smell of the sample or specimen',
            'format': 'text',
            'hstore': 'other',
            'valid': {
                'validate': 'any',
                'input_title': 'Smell',
                'input_message': 'Smell'
            }
            },

    # ==============================================================================
    # Personnel
    # ==============================================================================
    # FROM TABLE
    {'name': 'recordedBy_name',
              'disp_name': 'Recorded By (Name)',
              'description': '''Full name of who has recorded/analysed the data.
Can be a concatenated list, separated by: '|'
Example: John Doe | Ola Nordmann''',
              'dwcid': 'http://rs.tdwg.org/dwc/terms/recordedBy',
              'format': 'text',
              'hstore': False,
              'valid': {
                  'validate': 'any',
                  'input_title': 'Recorded By',
                  'input_message': '''Full name of who has recorded/analysed the data.
Can be a concatenated list, separated by: '|'
Example: John Doe | Ola Nordmann'''
              }
              },
    {'name': 'recordedBy_email',
              'disp_name': 'Recorded By (Email)',
              'description': '''Email of who has recorded/analysed the data.
Can be a concatenated list, separated by: '|'
Example: johnd@unis.no | olan@unis.no''',
              'dwcid': 'http://rs.tdwg.org/dwc/terms/recordedBy',
              'format': 'text',
              'hstore': False,
              'valid': {
                  'validate': 'any',
                  'input_title': 'Recorded By',
                  'input_message': '''Email of who has recorded/analysed the data.
Can be a concatenated list, separated by: '|'
Example: johnd@unis.no | olan@unis.no'''
              }
              },
    {'name': 'recordedBy_institution',
              'disp_name': 'Recorded By (Institution)',
              'description': '''Institution of who has recorded/analysed the data.
Can be a concatenated list, separated by: '|'. Please include for everyone listed, even if some are from the same institution.
Example: University Centre in Svalbard | University Centre in Svalbard''',
              'dwcid': 'http://rs.tdwg.org/dwc/terms/recordedBy',
              'format': 'text',
              'hstore': False,
              'valid': {
                  'validate': 'any',
                  'input_title': 'Recorded By',
                  'input_message': '''Institution of who has recorded/analysed the data.
Can be a concatenated list, separated by: '|'. Please include for everyone listed, even if some are from the same institution.
Example: University Centre in Svalbard | University Centre in Svalbard'''
              }
              },
    # FROM TABLE, LINK TO EMAIL AND INSTITUTION AUTOMATICALLY. WHAT ABOUT WHEN PI CHANGES INSTITUTION?
    {'name': 'pi_name',
              'disp_name': 'PI name',
              'description': '''Full name of the principal investigator of the data.
Can be a concatenated list, separated by: '|'
Example: John Doe | Ola Nordmann''',
              'format': 'text',
              'hstore': False,
              'valid': {
                  'validate': 'any',
                  'input_title': 'PI name',
                  'input_message': '''Full name of the principal investigator of the data.
Can be a concatenated list, separated by: '|'
Example: John Doe | Ola Nordmann'''
              }
              },
    {'name': 'pi_email',
              'disp_name': 'PI email',
              'description': '''Email of the principal investigator of the data.
Can be a concatenated list, separated by: '|'
Please include for every PI listed.
Example: john.doe@unis.no | ola.nordmann@unis.no''',
              'format': 'text',
              'hstore': False,
              'valid': {
                  'validate': 'any',
                  'input_title': 'PI email',
                  'input_message': '''Email of the principal investigator of the data.
Can be a concatenated list, separated by: '|'
Please include for every PI listed.
Example: john.doe@unis.no | ola.nordmann@unis.no'''
              }
              },
    {'name': 'pi_institution',
              'disp_name': 'PI institution',
              'description': '''Main institution of the principal investigator of the data.
Please include for every PI listed, even if the same.
Example: University Centre in Svalbard | University Centre in Svalbard''',
              'format': 'text',
              'hstore': False,
              'valid': {
                  'validate': 'any',
                  'input_title': 'PI institution',
                  'input_message': '''Main institution of the principal investigator of the data.
Please include for every PI listed, even if the same.
Example: University Centre in Svalbard | University Centre in Svalbard'''
              }
              },

    # ==============================================================================
    # Storage
    # ==============================================================================
    # Dropdown
    {'name': 'storageTemp',
               'disp_name': 'Storage temp',
               'description': 'Choose the storage temperature used',
               'format': 'text',
               'hstore': 'other',
               'width': 15,
               'valid': {
                   'validate': 'list',
                   'source': [
                       'neg 196 C (LN)',
                       'neg 80 C',
                       'neg 20 C',
                       'Cool room',
                       'Room temp'],
                   'input_title': 'Storage temperature',
                   'input_message': '''Choose the storage temperature used''',
                   'error_title': 'Error',
                   'error_message': 'Not a valid storage temperature'
               }
               },
    {'name': 'fixative',
            'disp_name': 'Fixative',
            'description': 'Fixative used for sample',
            'format': 'text',
            'hstore': 'other',
            'valid': {
                'validate': 'any',
                'input_title': 'Fixative',
                'input_message': '''Fixative used for sample '''
            }
            },
    # RETHINK. DEFAULT VALUE FOR NO PHYSICAL SAMPLE PRESERVED?
    {'name': 'sampleLocation',
                  'disp_name': 'Sample Location',
                  'description': '''The long-term storage location onshore, immediately after the cruise.
This could for instance be an institution or something more specific.''',
                  'format': 'text',
                  'hstore': False,
                  'valid': {
                      'validate': 'any',
                      'input_title': 'Sample Location',
                      'input_message': '''The long-term storage location onshore, immediately after the cruise.
This could for instance be an institution or something more specific.'''
                  }
                  },
    {'name': 'dilution_factor',
                   'disp_name': 'Dilution factor',
                   'description': 'Factor by which the sample has been diluted by',
                   'format': 'int',
                   'hstore': 'other',
                   'width': 20,
                   'valid': {
                       'validate': 'integer',
                       'criteria': '>',
                       'value': 0,
                       'input_title': 'Dilution factor',
                       'input_message': '''Positive integer''',
                       'error_title': 'Error',
                       'error_message': 'Integer > 0'
                   }
                   },
    {'name': 'sample_owner',
              'disp_name': 'Sample Owner',
              'description': 'Person or institution who owns the sample',
              'format': 'text',
              'hstore': 'other',
              'valid': {
                  'validate': 'any',
                  'input_title': 'Sample Owner',
                  'input_message': '''Person who owns the sample'''
              }
              },

    # ==============================================================================
    # Filtering
    # ==============================================================================
    {'name': 'filter',
          'disp_name': 'Filter',
          'description': '''Choose the filter used.
If no filtering is being done choose None''',
          'format': 'text',
          'hstore': 'other',
          'width': 15,
          'valid': {
              'validate': 'list',
              'source': ['None', 'GFF', '10 µm'],
              'input_title': 'Filter',
              'input_message': '''Choose the filter used.
If no filtering is being done choose None''',
              'error_title': 'Error',
              'error_message': 'Not a valid filter'
          }
          },
    {'name': 'filteredVolumeInMilliliters',
                               'disp_name': 'Filtered volume (mL)',
                               'description': 'Filtered volume in decimal millilitres',
                               'format': 'double precision',
                               'hstore': 'other',
                               'valid': {
                                   'validate': 'decimal',
                                   'criteria': '>',
                                   'value': 0,
                                   'input_title': 'Filtered volume (mL)',
                                   'input_message': '''Filtered volume in decimal millilitres''',
                                   'error_title': 'Error',
                                   'error_message': 'Decimal > 0'
                               }
                               },
    {'name': 'methanol_vol',
                'disp_name': 'Methanol volume (mL)',
                'description': 'Volume of methanol used in millilitres',
                'format': 'double precision',
                'hstore': 'other',
                'units': 'mL',
                'valid': {
                    'validate': 'decimal',
                    'criteria': '>',
                    'value': 0,
                    'input_title': 'Methanol volume (mL)',
                    'input_message': '''Volume of methanol used in millilitres''',
                    'error_title': 'Error',
                    'error_message': 'Decimal > 0'
                }
                },
    {'name': 'sampleVolumeInMilliliters',
                             'disp_name': 'Sample volume (mL)',
                             'description': 'Sample volume in millilitres',
                             'format': 'double precision',
                             'hstore': 'other',
                             'units': 'mL',
                             'valid': {
                                 'validate': 'decimal',
                                 'criteria': '>',
                                 'value': 0,
                                 'input_title': 'Sample volume (mL)',
                                 'input_message': '''Sample volume in millilitres''',
                                 'error_title': 'Error',
                                 'error_message': 'Decimal > 0'
                             }
                             },
    {'name': 'subsample_vol',
                 'disp_name': 'Subsample volume (mL)',
                 'description': 'Subsample volume in millilitres',
                 'units': 'mL',
                 'format': 'double precision',
                 'hstore': 'other',
                 'valid': {
                     'validate': 'decimal',
                     'criteria': '>',
                     'value': 0,
                     'input_title': 'Subsample volume (mL)',
                     'input_message': '''Subsample volume in millilitres''',
                     'error_title': 'Error',
                     'error_message': 'Decimal > 0'
                 }
                 },

    # ==============================================================================
    # Darwin Core Terms
    # ==============================================================================
    {'name': 'individualCount',
                   'disp_name': 'Individual Count',
                   'description': 'The number of individuals present at the time of the Occurrence.',
                   'format': 'int',
                   'hstore': 'other',
                   'width': 20,
                   'units': '1',
                   'dwcid': 'https://dwc.tdwg.org/terms/#dwc:individualCount',
                   'valid': {
                       'validate': 'integer',
                       'criteria': '>',
                       'value': 0,
                       'input_title': 'Abundance',
                       'input_message': '''The number of individuals present at the time of the Occurrence.''',
                       'error_title': 'Error',
                       'error_message': 'Integer > 0'
                   }
                   },
    {'name': 'taxon',
            'disp_name': 'Taxon',
            'description': 'A group of organisms considered by taxonomists to form a homogeneous unit.',
            'format': 'text',
            'hstore': 'other',
            'dwcid': 'http://rs.tdwg.org/dwc/terms/Taxon',
            'valid': {
                'validate': 'any',
                'input_title': 'Taxon',
                'input_message': 'A group of organisms considered by taxonomists to form a homogeneous unit.'
            }
            },
    {'name': 'phylum',
            'disp_name': 'Phylum',
            'description': 'The full scientific name of the phylum or division in which the taxon is classified.',
            'format': 'text',
            'hstore': 'other',
            'dwcid': 'https://dwc.tdwg.org/terms/#dwc:phylum',
            'valid': {
                'validate': 'any',
                'input_title': 'Phylum',
                'input_message': 'The full scientific name of the phylum or division in which the taxon is classified.'
            }
            },
    {'name': 'sex',
       'disp_name': 'Sex',
       'description': '''Gender of the specimen.
Male (M), female (F), maybe male (M?), maybe female (F?) or unknown (?)''',
       'format': 'text',
       'hstore': 'other',
       'dwcid': 'http://rs.tdwg.org/dwc/terms/sex',
                'valid': {
                    'validate': 'any',
                    # 'source': ['Male', 'Female', 'Undetermined'],
                    'input_title': 'Sex',
                    'input_message': '''Male (M), female (F), maybe male (M?), maybe female (F?) or unknown (?)''',
                    # 'error_title': 'Error',
                    # 'error_message': 'Not a valid sex '
                }
       },
    {'name': 'kingdom',
       'disp_name': 'Kingdom',
       'description': 'The full scientific name of the kingdom in which the taxon is classified.',
       'format': 'text',
       'hstore': 'other',
       'dwcid': 'https://dwc.tdwg.org/terms/#dwc:kingdom',
                'valid': {
                    'validate': 'any',
                    # 'source': ['Animalia', 'Archaea', 'Bacteria', 'Chromista', 'Fungi', 'Plantae', 'Protozoa', 'Viruses'],
                    'input_title': 'Kingdom',
                    'input_message': '''The full scientific name of the kingdom in which the taxon is classified.''',
                }
       },
    {'name': 'class',
       'disp_name': 'Class',
       'description': 'The full scientific name of the class in which the taxon is classified.',
       'format': 'text',
       'hstore': 'other',
       'dwcid': 'https://dwc.tdwg.org/list/#dwc_class',
                'valid': {
                    'validate': 'any',
                    'input_title': 'Class',
                    'input_message': 'The full scientific name of the class in which the taxon is classified.'
            }
       },
    {'name': 'order',
       'disp_name': 'Order',
       'description': 'The full scientific name of the order in which the taxon is classified.',
       'format': 'text',
       'hstore': 'other',
       'dwcid': 'https://dwc.tdwg.org/terms/#dwc:order',
                'valid': {
                    'validate': 'any',
                    'input_title': 'Order',
                    'input_message': 'The full scientific name of the order in which the taxon is classified.'
            }
       },
    {'name': 'family',
       'disp_name': 'Family',
       'description': 'The full scientific name of the family in which the taxon is classified.',
       'format': 'text',
       'hstore': 'other',
       'dwcid': 'https://dwc.tdwg.org/list/#dwc_family',
                'valid': {
                    'validate': 'any',
                    'input_title': 'Family',
                    'input_message': 'The full scientific name of the family in which the taxon is classified.'
            }
       },
    {'name': 'scientificName',
                  'disp_name': 'Scientific Name',
                  'description': '''The full scientific name, with authorship and date information if known.
When forming part of an Identification, this should be the name in lowest level taxonomic rank that can be determined''',
                  'format': 'text',
                  'hstore': 'other',
                  'width': 20,
                  'dwcid': 'http://rs.tdwg.org/dwc/terms/scientificName',
                  'valid': {
                      'validate': 'any',
                      'input_title': 'Scientific Name',
                      'input_message': '''The full scientific name, with authorship and date information if known.
When forming part of an Identification, this should be the name in lowest level taxonomic rank that can be determined'''
                  },
                  'cell_format': {
                      'left': True
                  }
                  },
    {'name': 'samplingProtocolDoc',
                    'disp_name': 'Sampling protocol document',
                    'description': '''This should be a reference to the document that contains the sampling protocol used.
Where possible, include the DOI of the document.''',
                    'format': 'text',
                    'hstore': False,
                    'dwcid': 'https://dwc.tdwg.org/terms/#dwc:samplingProtocol',
                    'valid': {
                        'validate': 'any',
                        'input_title': 'Sampling protocol',
                        'input_message': '''This should be a reference to the document that contains the sampling protocol used.
Where possible, include the DOI of the document.'''
                    }
                    },
    {'name': 'samplingProtocolSection',
                    'disp_name': 'Sampling protocol section',
                    'description': '''This should be a reference to the section within sampling protocol document.''',
                    'format': 'text',
                    'hstore': False,
                    'dwcid': 'https://dwc.tdwg.org/terms/#dwc:samplingProtocol',
                    'valid': {
                        'validate': 'any',
                        'input_title': 'Sampling protocol',
                        'input_message': '''This should be a reference to the section within sampling protocol document.'''
                    }
                    },
    {'name': 'samplingProtocolVersion',
                    'disp_name': 'Sampling protocol version',
                    'description': '''This should be a reference to the version of the sampling protocol document.
This is not neccessary if you have included the DOI in the sampling protocol document.''',
                    'format': 'text',
                    'hstore': False,
                    'dwcid': 'https://dwc.tdwg.org/terms/#dwc:samplingProtocol',
                    'valid': {
                        'validate': 'any',
                        'input_title': 'Sampling protocol',
                        'input_message': '''This should be a reference to the version of the sampling protocol document.
                        This is not neccessary if you have included the DOI in the sampling protocol document.'''
                    }
                    },

    # ==============================================================================
    # Probable MeasurementOrFact types from Darwin Core
    # ==============================================================================
    {'name': 'weightInGrams',
                 'disp_name': 'Weight (g)',
                 'description': 'Weight of the sample or specimen in grams',
                 'format': 'double precision',
                 'hstore': 'other',
                 'units': 'g',
                 'valid': {
                     'validate': 'decimal',
                     'criteria': '>',
                     'value': 0,
                     'input_title': 'Weight in grams (g)',
                     'input_message': '''Weight in grams''',
                     'error_title': 'Error',
                     'error_message': 'Float > 0'
                 }
                 },
    {'name': 'gonadWeightInGrams',
                      'disp_name': 'Gonad Weight (g)',
                      'description': 'Wet weight of the gonad in in grams',
                      'format': 'double precision',
                      'hstore': 'other',
                      'units': 'g',
                      #                  'dwcid': 'http://rs.tdwg.org/dwc/terms/dynamicProperties',
                      'valid': {
                          'validate': 'decimal',
                          'criteria': '>',
                          'value': 0,
                          'input_title': 'Gonad Weight in grams (g)',
                          'input_message': '''Wet weight of the gonad in in grams''',
                          'error_title': 'Error',
                          'error_message': 'Float > 0'
                      }
                      },
    {'name': 'liverWeightInGrams',
                      'disp_name': 'Liver Weight (g)',
                      'description': 'Wet weight of the liver in in grams',
                      'format': 'double precision',
                      'hstore': 'other',
                      'units': 'g',
                      #                  'dwcid': 'http://rs.tdwg.org/dwc/terms/dynamicProperties',
                      'valid': {
                          'validate': 'decimal',
                          'criteria': '>',
                          'value': 0,
                          'input_title': 'Liver Weight in grams (g)',
                          'input_message': '''Wet weight of the liver in in grams''',
                          'error_title': 'Error',
                          'error_message': 'Float > 0'
                      }
                      },
    {'name': 'somaticWeightInGrams',
                        'disp_name': 'Somatic Weight (g)',
                        'description': 'Wet weight of the fish when all inner organs are removed from the fish gonad in in grams',
                        'format': 'double precision',
                        'hstore': 'other',
                        'units': 'g',
                        #                  'dwcid': 'http://rs.tdwg.org/dwc/terms/dynamicProperties',
                        'valid': {
                            'validate': 'decimal',
                            'criteria': '>',
                            'value': 0,
                            'input_title': 'Somatic Weight in grams (g)',
                            'input_message': '''Wet weight of the fish when all inner organs are removed from the fish gonad in in grams''',
                            'error_title': 'Error',
                            'error_message': 'Float > 0'
                        }
                        },
    {'name': 'forkLengthInMeters',
                      'disp_name': 'Fork lenght (cm)',
                      'description': '''The length of a fish measured from the most anterior part of the head to the deepest point of the notch in the tail fin in cm.
Positive decimal number''',
                      'format': 'double precision',
                      'hstore': 'other',
                      'units': 'cm',
                      #                  'dwcid': 'http://rs.tdwg.org/dwc/terms/dynamicProperties',
                      'valid': {
                          'validate': 'decimal',
                          'criteria': '>',
                          'value': 0,
                          'input_title': 'Fork lenght (cm)',
                          'input_message': '''The length of a fish measured from the most anterior part of the head to the deepest point of the notch in the tail fin in cm.
Positive decimal number''',
                          'error_title': 'Error',
                          'error_message': 'Float > 0'
                      }
                      },
    {'name': 'maturationStage',
                   'disp_name': 'Maturation Stage',
                   'description': '''On the basis of shape, size, color of the gonads and other morphological featuers, at least six maturity stages can be recongnized
Value in range [0, 7]''',
                   'format': 'int',
                   'hstore': 'other',
                   'units': '1',
                   'valid': {
                       'validate': 'integer',
                       'criteria': 'between',
                       'minimum': 0,
                       'maximum': 7,
                       'input_title': 'Maturation Stage',
                       'input_message': '''On the basis of shape, size, color of the gonads and other morphological featuers, at least six maturity stages can be recongnized
Value in range [0, 7]''',
                       'error_title': 'Error',
                       'error_message': 'Int range [0, 7]'
                   }
                   },
    {'name': 'ectoparasites',
                 'disp_name': 'Ectoparasites',
                 'description': '''Number of ectoparasites visible on the fins and gills of the fish
Integer >= 0''',
                 'format': 'int',
                 'hstore': 'other',
                 'units': '1',
                 'valid': {
                     'validate': 'integer',
                     'criteria': '>=',
                     'value': 0,
                     'input_title': 'Ectoparasites',
                     'input_message': '''Number of ectoparasites visible on the fins and gills of the fish
Integer >= 0''',
                     'error_title': 'Error',
                     'error_message': 'Int range [0, 7]' # is this right?
                 }
                 },
    {'name': 'endoparasites',
                 'disp_name': 'Endoparasites',
                 'description': '''Number of endoparasites visible in the body cavity of the fish
Integer >= 0''',
                 'format': 'int',
                 'hstore': 'other',
                 'units': '1',
                 'valid': {
                     'validate': 'integer',
                     'criteria': '>=',
                     'value': 0,
                     'input_title': 'Endoparasites',
                     'input_message': '''Number of endoparasites visible in the body cavity of the fish
Integer >= 0''',
                     'error_title': 'Error',
                     'error_message': 'Int range [0, 7]'
                 }
                 },

    # ==============================================================================
    # CF standard names and other physical properties and physical oceanography things
    # ==============================================================================
    {'name': 'seaIceCoreType',
                  'disp_name': 'Sea Ice Core Type',
                  'description': 'The analysis the sea ice core is intended for',
                  'format': 'text',
                  'hstore': 'other',
                  'valid': {
                      'validate': 'any',
                      'input_title': 'Sea Ice Core Type',
                      'input_message': 'The analysis the sea ice core is intended for'
                  }
                  },
    {'name': 'seaIceCoreLengthInMeters',
                            'disp_name': 'Sea Ice Core Length (cm)',
                            'description': '''Sea ice core length in decimal centimeters.
Float number larger than 0 ''',
                            'units': 'cm',
                            'format': 'double precision',
                            'hstore': 'other',
                            'valid': {
                                'validate': 'decimal',
                                'criteria': '>',
                                'value': 0,
                                'input_title': 'Sea Ice Core length (cm)',
                                'input_message': '''Sea ice core length in decimal centimeters.
 Float number larger than 0 ''',
                                'error_title': 'Error',
                                'error_message': 'Float > 0'
                            }
                            },
    {'name': 'seaIceThicknessInMeters',
                           'disp_name': 'Sea Ice Thickness (cm)',
                           'description': '''Sea ice thickness in decimal centimeters.
Float number larger than 0 ''',
                           'units': 'cm',
                           'format': 'double precision',
                           'hstore': 'other',
                           'valid': {
                               'validate': 'decimal',
                               'criteria': '>',
                               'value': 0,
                               'input_title': 'Sea Ice Thickness (cm)',
                               'input_message': '''Sea ice thickness in decimal centimeters.
 Float number larger than 0 ''',
                               'error_title': 'Error',
                               'error_message': 'Float > 0'
                           }
                           },
    {'name': 'seaIceFreeboardInMeters',
                           'disp_name': 'Sea Ice Freeboard (cm)',
                           'description': '''The height of the sea ice surface relative to the adjacent sea in decimal centimeters.
Float number larger than 0 ''',
                           'units': 'cm',
                           'format': 'double precision',
                           'hstore': 'other',
                           'valid': {
                               'validate': 'decimal',
                               'criteria': '>',
                               'value': 0,
                               'input_title': 'Sea Ice Freeboard (cm)',
                               'input_message': '''Sea ice freeboard in decimal centimeters.
 Float number larger than 0 ''',
                               'error_title': 'Error',
                               'error:message': 'Float > 0'
                           }
                           },
    {'name': 'seaIceMeltpondTemperatureInCelsius',
                                       'disp_name': 'Sea Ice Meltpond Temperature (C)',
                                       'description': '''Sea ice meltpond temperature in Celsius.
Float number larger than -10 ''',
                                       'units': 'Celsius',
                                       'format': 'double precision',
                                       'hstore': 'other',
                                       'valid': {
                                           'validate': 'decimal',
                                           'criteria': '>',
                                           'value': -10,
                                           'input_title': 'Sea Ice Meltpond Temperature (C)',
                                           'input_message': '''Sea ice meltpond temperature in Celsius.
 Float number larger than -10 ''',
                                           'error_title': 'Error',
                                           'error:message': 'Float > -10'
                                       }
                                       },
    {'name': 'seaIceMeltpondSalinity',
                          'disp_name': 'Sea Ice Meltpond Salinity (1e-3)',
                          'description': '''Sea ice meltpond salinity in parts per thousand
Often using the Practical Salinity Scale of 1978
Float number larger than or equal to 0
Example: 0.029''',
                          'units': '1e-3',
                          'format': 'double precision',
                          'hstore': 'other',
                          'valid': {
                              'validate': 'decimal',
                              'criteria': '>=',
                              'value': 0,
                              'input_title': 'Sea Ice Meltpond Salinity',
                              'input_message': '''Sea ice meltpond salinity in parts per thousand
Often using the Practical Salinity Scale of 1978
Float number larger than or equal to 0
Example: 0.029''',
                              'error_title': 'Error',
                              'error_message': 'Float >= 0'
                          }
                          },
    {'name': 'seaWaterTemperatueInCelsius',
                               'disp_name': 'Sea Water Temp (C)',
                               'description': '''Sea water temperature in Celsius
Float number larger than -10 degrees C''',
                               'inherit': True,
                               'format': 'double precision',
                               'hstore': 'other',
                               'units': 'Celsius',
                               'cf_name': 'sea_water_temperature',
                               'valid': {
                                   'validate': 'decimal',
                                   'criteria': '>',
                                   'value': -10,
                                   'input_title': 'Sea Water Temp (C)',
                                   'input_message': '''Sea water temperature in Celsius
Float number larger than -10 degrees C''',
                                   'error_title': 'Error',
                                   'error_message': 'Float > -10 C'
                               }
                               },
    {'name': 'seaWaterPracticalSalinity',
                             'disp_name': 'Sea Water Practical Salinity (1)',
                             'description': '''Practical Salinity, S_P, is a determination of
the salinity of sea water, based on its electrical conductance.
The measured conductance, corrected for temperature and pressure,
is compared to the conductance of a standard potassium chloride
solution, producing a value on the Practical Salinity Scale of 1978 (PSS-78).
Float number larger than or equal to 0
Example: 29.003''',
                             'inherit': True,
                             'format': 'double precision',
                             'hstore': 'other',
                             'units': '1',
                             'cf_name': 'sea_water_practical_salinity',
                             'valid': {
                                 'validate': 'decimal',
                                 'criteria': '>=',
                                 'value': 0,
                                 'input_title': 'Sea Water Practical Salinity',
                                 'input_message': '''Practical Salinity, S_P, is a determination of
the salinity of sea water, based on its electrical conductance.
The measured conductance, corrected for temperature and pressure,
is compared to the conductance of a standard potassium chloride
solution, producing a value on the Practical Salinity Scale of 1978 (PSS-78).
Float number larger than or equal to 0
Example: 29.003''',
                                 'error_title': 'Error',
                                 'error_message': 'Float >= 0'
                             }
                             },
    {'name': 'seaWaterAbsoluteSalinity',
                            'disp_name': 'Sea Water Absolute Salinity (g/kg)',
                            'description': '''Absolute Salinity, S_A, is defined as part of
the Thermodynamic Equation of Seawater 2010 (TEOS-10) which was
adopted in 2010 by the Intergovernmental Oceanographic
Commission (IOC). It is the mass fraction of dissolved material
in sea water.
Float number larger than or equal to 0
Example: 3.5''',
                            'inherit': True,
                            'units': 'g kg-1',
                            'format': 'double precision',
                            'hstore': 'other',
                            'cf_name': 'sea_water_absolute_salinity',
                            'valid': {
                                'validate': 'decimal',
                                'criteria': '>=',
                                'value': 0,
                                'input_title': 'Sea Water Absolute Salinity',
                                'input_message': '''Absolute Salinity, S_A, is defined as part of
the Thermodynamic Equation of Seawater 2010 (TEOS-10) which was
adopted in 2010 by the Intergovernmental Oceanographic
Commission (IOC). It is the mass fraction of dissolved material
in sea water.
Float number larger than or equal to 0
Example: 3.5''',
                                'error_title': 'Error',
                                'error_message': 'Float >= 0'
                            }
                            },
    {'name': 'seaWaterElectricalConductivity',
                                  'disp_name': 'Sea Water Conductivity (S/m)',
                                  'description': '''Sea water electrical conductivity in siemens per meter
Float number larger than or equal to 0
Example: 3.0''',
                                  'inherit': True,
                                  'format': 'double precision',
                                  'hstore': 'other',
                                  'units': 's m-1',
                                  'cf_name': 'sea_water_electrical_conductivity',
                                  'valid': {
                                      'validate': 'decimal',
                                      'criteria': '>=',
                                      'value': 0,
                                      'input_title': 'Sea Water Conductivity',
                                      'input_message': '''Sea water electrical conductivity in siemens per meter
Float number larger than or equal to 0
Example: 3.0''',
                                      'error_title': 'Error',
                                      'error_message': 'Float >= 0'
                                  }
                                  },
    {'name': 'seaWaterPressure',
                    'disp_name': 'Sea Water Pressure (dbar)',
                    'description': '''Sea water pressure in decibar
Float number larger than 0''',
                    'inherit': True,
                    'format': 'double precision',
                    'hstore': 'other',
                    'units': 'dbar',
                    'cf_name': 'sea_water_pressure',
                    'valid': {
                        'validate': 'decimal',
                        'criteria': '>',
                        'value': 0,
                        'input_title': 'Sea Water Pressure (dbar)',
                        'input_message': '''Sea water pressure in decibar
Float number larger than 0''',
                        'error_title': 'Error',
                        'error_message': 'Float > 0'
                    }
                    },
    {'name': 'seaWaterChlorophyllA',
                        'disp_name': 'Sea Chl A (mg/m^3)',
                        'description': '''Sea Water Chlorophyll A in milligrams per cubic meter
Positive float number (>= 0)''',
                        'format': 'double precision',
                        'hstore': 'other',
                        'units': 'mg m-3',
                        'cf_name': 'mass_concentration_of_chlorophyll_a_in_sea_water',
                        'valid': {
                            'validate': 'decimal',
                            'criteria': '>=',
                            'value': 0,
                            'input_title': 'Sea Water Chlorophyll A (mg/m^3)',
                            'input_message': '''
Sea Water Chlorophyll A in milligrams per cubic meter
Positive float number (>= 0)''',
                            'error_title': 'Error',
                            'error_message': 'Float >= 0'
                        }
                        },
    {'name': 'seaWaterPhaeopigment',
                        'disp_name': 'Sea Phaeo (mg/m^3)',
                        'description': '''Sea Water Phaeopigment in milligrams per cubic meter.
Positive float number''',
                        'format': 'double precision',
                        'hstore': 'other',
                        'units': 'mg m-3',
                        'cf_name': 'mass_concentration_of_phaeopigments_in_sea_water',
                        'valid': {
                            'validate': 'decimal',
                            'criteria': '>',
                            'value': 0,
                            'input_title': 'Sea Water Phaeopigment (mg/m^3)',
                            'input_message': '''
Sea Water Phaeopigment in milligrams per cubic meter
Positive float number''',
                            'error_title': 'Error',
                            'error_message': 'Float > 0'
                        }
                        },
    {'name': 'seaIceChlorophyllA',
                      'disp_name': 'Ice Chl A (mg/m^3)',
                      'description': '''Sea ice Chlorophyll A in milligrams per cubic meter
Positive float number (>= 0)''',
                      'format': 'double precision',
                      'hstore': 'other',
                      'units': 'mg m-3',
                      'cf_name': 'mass_concentration_of_chlorophyll_a_in_sea_ice',
                      'valid': {
                          'validate': 'decimal',
                          'criteria': '>=',
                          'value': 0,
                          'input_title': 'Sea Ice Chlorophyll a (mg/m^3)',
                          'input_message': '''
Sea Ice Chlorophyll in milligrams per cubic meter
Positive float number (>= 0)''',
                          'error_title': 'Error',
                          'error_message': 'Float >= 0'
                      }
                      },
    {'name': 'seaIcePhaeopigment',
                      'disp_name': 'Ice Phaeo (mg/m^3)',
                      'description': '''Sea Ice Phaeopigment in milligrams per cubic meter
Positive float number''',
                      'format': 'double precision',
                      'hstore': 'other',
                      'units': 'mg m-3',
                      'cf_name': 'mass_concentration_of_phaeopigments_in_sea_ice',
                      'valid': {
                          'validate': 'decimal',
                          'criteria': '>',
                          'value': 0,
                          'input_title': 'Sea Ice Phaeopigment (mg/m^3)',
                          'input_message': '''
Sea Ice Phaeopigment in milligrams per cubic meter
Positive float number''',
                          'error_title': 'Error',
                          'error_message': 'Float > 0'
                      }
                      },
    {'name': 'sedimentChlorophyllA',
                        'disp_name': 'Sediment Chl A (mg/m^3)',
                        'description': '''
Sediment Chlorophyll A in milligrams per cubic meter
Positive float number (>= 0)''',
                        'format': 'double precision',
                        'hstore': 'other',
                        'units': 'mg m-3',
                        'valid': {
                            'validate': 'decimal',
                            'criteria': '>=',
                            'value': 0,
                            'input_title': 'Sediment Chlorophyll a (mg/m^3)',
                            'input_message': '''
Sediment Chlorophyll in milligrams per cubic meter
Positive float number (>= 0)''',
                            'error_title': 'Error',
                            'error_message': 'Float >= 0'
                        }
                        },
    {'name': 'sedimentPhaeopigment',
                        'disp_name': 'Sediment Phaeo (mg/m^3)',
                        'description': '''
Sediment Phaeopigment in milligrams per cubic meter
Positive float number''',
                        'format': 'double precision',
                        'hstore': 'other',
                        'units': 'mg m-3',
                        'valid': {
                            'validate': 'decimal',
                            'criteria': '>',
                            'value': 0,
                            'input_title': 'Sediment Phaeopigment (mg/m^3)',
                            'input_message': '''
Sediment Phaeopigment in milligrams per cubic meter
Positive float number''',
                            'error_title': 'Error',
                            'error_message': 'Float > 0'
                        }
                        },
    {'name': 'sedimentPH',
              'disp_name': 'Sediment pH  (total scale)',
              'description': '''
Is the measure of acidity of seawater, defined as the negative logarithm of
the concentration of dissolved hydrogen ions plus bisulfate ions in a sea water
medium; it can be measured or calculated; when measured the scale is defined
according to a series of buffers prepared in artificial seawater containing
bisulfate.
Float in range [-2, 16]''',
              'format': 'double precision',
              'hstore': 'other',
              'units': '1',
              'valid': {
                  'validate': 'decimal',
                  'criteria': 'between',
                  'minimum': -2,
                  'maximum': 16,
                  'input_title': 'Sediment  pH  (total scale)',
                  'input_message': '''
Is the measure of acidity of seawater, defined as the negative logarithm of
the concentration of dissolved hydrogen ions plus bisulfate ions in a sea water
medium; it can be measured or calculated; when measured the scale is defined
according to a series of buffers prepared in artificial seawater containing
bisulfate.
Float in range [-2, 16]''',
                  'error_title': 'Error',
                  'error_message': 'Not in range [-2, 16]'
              }
              },
    {'name': 'sedimentTOC',
               'disp_name': 'Sediment TOC (mg/L)',
               'description': '''
Sediment Total Organic Carbon in milligrams per litre
Positive float number''',
               'format': 'double precision',
               'hstore': 'other',
               'units': 'mg L-1',
               'valid': {
                   'validate': 'decimal',
                   'criteria': '>=',
                   'value': 0,
                   'input_title': 'Sediment TOC (mg/L)',
                   'input_message': '''
Sediment Total Organic Carbon in milligrams per litre
Positive float number''',
                   'error_title': 'Error',
                   'error_message': 'Float >= 0'
               }
               },
    {'name': 'sedimentTN',
              'disp_name': 'Sediment TN (mg/L)',
              'description': '''
Sediment Total Nitrogen in milligrams per litre
Positive float number''',
              'format': 'double precision',
              'hstore': 'other',
              'units': 'mg L-1',
              'valid': {
                  'validate': 'decimal',
                  'criteria': '>=',
                  'value': 0,
                  'input_title': 'Sediment TN (mg/L)',
                  'input_message': '''
Sediment Total Nitrogen in milligrams per litre
Positive float number''',
                  'error_title': 'Error',
                  'error_message': 'Float >= 0'
              }
              },
    {'name': 'benthicRespiration',
                      'disp_name': 'Benthic Respiration (mmol/m^2)',
                      'description': '''
Benthic respiration of Oxygen in millimole per square meter
Positive float number''',
                      'format': 'double precision',
                      'hstore': 'other',
                      'units': 'mmol m-2',
                      'valid': {
                          'validate': 'decimal',
                          'criteria': '>=',
                          'value': 0,
                          'input_title': 'Benthic Respiration (mmol/m^2)',
                          'input_message': '''
Benthic respiration of Oxygen in millimole per square meter
Positive float number''',
                          'error_title': 'Error',
                          'error_message': 'Float >= 0'
                      }
                      },
    {'name': 'seaWaterTotalDIC',
                    'disp_name': 'Sea DIC (umol/kg)',
                    'description': '''
Sea Water Total dissolved inorganic carbon in umol per kg
Positive float number''',
                    'format': 'double precision',
                    'hstore': 'other',
                    'units': 'umol kg-1',
                    'cf_name': 'mole_concentration_of_dissolved_inorganic_carbon_in_sea_water',
                    'valid': {
                        'validate': 'decimal',
                        'criteria': '>=',
                        'value': 0,
                        'input_title': 'Sea Water DIC (umol/kg)',
                        'input_message': '''
Sea Water Total dissolved inorganic carbon in umol per kg
Positive float number''',
                        'error_title': 'Error',
                        'error_message': 'Float >= 0'
                    }
                    },
    {'name': 'seaIceTotalDIC',
                  'disp_name': 'Ice DIC (umol/kg)',
                  'description': '''
Sea Ice Total dissolved inorganic carbon in umol per kg
Positive float number''',
                  'format': 'double precision',
                  'hstore': 'other',
                  'units': 'umol kg-1',
                  'valid': {
                      'validate': 'decimal',
                      'criteria': '>=',
                      'value': 0,
                      'input_title': 'Sea Ice DIC (umol/kg)',
                      'input_message': '''
Sea Ice Total dissolved inorganic carbon in umol per kg
Positive float number''',
                      'error_title': 'Error',
                      'error_message': 'Float >= 0'
                  }
                  },
    {'name': 'seaWaterDeltaO18',
                    'disp_name': 'Sea delta-O-18 (1e-3)',
                    'description': '''
Sea Water delta-O-18 in parts per thousand
Positive float number''',
                    'format': 'double precision',
                    'hstore': 'other',
                    'units': '1e-3',
                    'valid': {
                        'validate': 'decimal',
                        'criteria': '>=',
                        'value': 0,
                        'input_title': 'Sea Water delta-O-18 (1e-3)',
                        'input_message': '''
Sea Water delta-O-18 in parts per thousand
Positive float number''',
                        'error_title': 'Error',
                        'error_message': 'Float >= 0'
                    }
                    },
    {'name': 'seaIceDeltaO18',
                  'disp_name': 'Ice delta-O-18 (1e-3)',
                  'description': '''
Sea Ice delta-O-18 in parts per thousand
Positive float number''',
                  'format': 'double precision',
                  'hstore': 'other',
                  'units': '1e-3',
                  'valid': {
                      'validate': 'decimal',
                      'criteria': '>=',
                      'value': 0,
                      'input_title': 'Sea Ice delta-O-18 (1e-3)',
                      'input_message': '''
Sea Ice delta-O-18 in parts per thousand
Positive float number''',
                      'error_title': 'Error',
                      'error_message': 'Float >= 0'
                  }
                  },
    {'name': 'seaWaterPH',
              'disp_name': 'Sea Water pH  (total scale)',
              'description': '''
Is the measure of acidity of seawater, defined as the negative logarithm of
the concentration of dissolved hydrogen ions plus bisulfate ions in a sea water
medium; it can be measured or calculated; when measured the scale is defined
according to a series of buffers prepared in artificial seawater containing
bisulfate.
Float in range [-2, 16]''',
              'format': 'double precision',
              'hstore': 'other',
              'units': '1',
              'cf_name': 'sea_water_ph_reported_on_total_scale',
              'valid': {
                  'validate': 'decimal',
                  'criteria': 'between',
                  'minimum': -2,
                  'maximum': 16,
                  'input_title': 'Sea Water pH  (total scale)',
                  'input_message': '''
Is the measure of acidity of seawater, defined as the negative logarithm of
the concentration of dissolved hydrogen ions plus bisulfate ions in a sea water
medium; it can be measured or calculated; when measured the scale is defined
according to a series of buffers prepared in artificial seawater containing
bisulfate.
Float in range [-2, 16]''',
                  'error_title': 'Error',
                  'error_message': 'Not in range [-2, 16]'
              }
              },
    {'name': 'seaWaterAlkalinity',
                      'disp_name': 'Total Alkalinity (umol/kg)',
                      'description': '''
Sea Water Total Alkalinity in micromols per kilogram
Positive float number''',
                      'format': 'double precision',
                      'hstore': 'other',
                      'units': 'umol kg-1',
                      'valid': {
                          'validate': 'decimal',
                          'criteria': '>=',
                          'value': 0,
                          'input_title': 'Sea Water Total Alkalinity (umol/kg)',
                          'input_message': '''
Sea Water Total Alkalinity in micromols per kilogram
Positive float number''',
                          'error_title': 'Error',
                          'error_message': 'Float >= 0'
                      }
                      },
    {'name': 'seaWaterTOC',
               'disp_name': 'TOC (mg/L)',
               'description': '''
Sea Water Total Organic Carbon in milligrams per litre
Positive float number''',
               'format': 'double precision',
               'hstore': 'other',
               'units': 'mg L-1',
               'valid': {
                   'validate': 'decimal',
                   'criteria': '>=',
                   'value': 0,
                   'input_title': 'TOC (mg/L)',
                   'input_message': '''
Sea Water Total Organic Carbon in milligrams per litre
Positive float number''',
                   'error_title': 'Error',
                   'error_message': 'Float >= 0'
               }
               },
    {'name': 'seaWaterPON',
               'disp_name': 'PON (ug/L)',
               'description': '''
Sea Water Quantification of particulate organic nitrogen in micrograms per litre
Positive float number''',
               'format': 'double precision',
               'hstore': 'other',
               'units': 'ug L-1',
               'valid': {
                   'validate': 'decimal',
                   'criteria': '>=',
                   'value': 0,
                   'input_title': 'PON (ug/L)',
                   'input_message': '''
Sea Water Quantification of particulate organic nitrogen in micrograms per litre
Positive float number''',
                   'error_title': 'Error',
                   'error_message': 'Float >= 0'
               }
               },
    {'name': 'seaWaterPOC',
               'disp_name': 'POC (ug/L)',
               'description': '''
Sea Water Quantification of particulate organic carbon  in micrograms per litre
Positive float number''',
               'format': 'double precision',
               'hstore': 'other',
               'units': 'ug L-1',
               'valid': {
                   'validate': 'decimal',
                   'criteria': '>=',
                   'value': 0,
                   'input_title': 'POC (ug/L)',
                   'input_message': '''
Sea Water Quantification of particulate organic carbon  in micrograms per litre
Positive float number''',
                   'error_title': 'Error',
                   'error_message': 'Float >= 0'
               }
               },

    # ==============================================================================
    # Sample details
    # ==============================================================================
    {'name': 'sampleType',
              'disp_name': 'Sample Type',
              'description': '''Choose the sample type.
Listed at: https://github.com/SIOS-Svalbard/AeN_doc/blob/master/list_sample_types.csv''',
              'long_list': True,
              'format': 'text',
              'hstore': False,
              'valid': {
                  'validate': 'list',
                  #'source': __sample_types,
                  'input_title': 'Sample type',
                  'input_message': '''Choose the sample type.
Listed at: https://github.com/SIOS-Svalbard/AeN_doc/blob/master/list_sample_types.csv''',
                  'error_title': 'Error',
                  'error_message': 'Not a valid sample type'
              }
              },
    # THIS SHOULD BECOME A MORE IMPORTANT TERM IN V2, AND MOST OF THE TERMS IN SAMPLE TYPE SHOULD BE MOVED TO INTENDED METHOD. MAKE REQUIRED TERM FOR SAMPLES.
    {'name': 'intendedMethod',
                  'disp_name': 'Intended Method',
                  'description': '''The intended measurement or analysis method for the sample.
If multiple methods, separate with ';'.
Examples: 'FCM', 'XCM', 'SEM' ''',
                  'format': 'text',
                  'hstore': False,
                  'valid': {
                      'validate': 'any',
                      'input_title': 'Intended Method',
                      'input_message': '''The intended measurement or analysis method for the sample.
If multiple methods, separate with ';'.
Examples: 'FCM', 'XCM', 'SEM' '''
                  }
                  },
    {'name': 'tissueType',
              'disp_name': 'Tissue Type',
              'description': '''The type of tissue in the sample.
If multiple tissue types, organs etc. separate with ';'.
Examples: 'heart', 'liver; brain', 'liver section' ''',
              'format': 'text',
              'hstore': 'other',
              'valid': {
                  'validate': 'any',
                  'input_title': 'Tissue Type',
                  'input_message': '''The type of tissue in the sample.
If multiple tissue types, organs etc. separate with ';'.
Examples: 'heart', 'liver; brain', 'liver section' '''
              }
              },

    # ==============================================================================
    # Instrumentation
    # ==============================================================================
    {'name': 'gearType',
                    'disp_name': 'Gear Type',
                    'description': '''Choose the gear used to retrieve the sample.
Listed at: https://github.com/SIOS-Svalbard/AeN_doc/blob/master/list_gear_types.csv''',
                    'inherit': True,
                    'format': 'text',
                    'hstore': False,
                    'long_list': True,
                    'valid': {
                        'validate': 'list',
                        #'source': __gear_types,
                        'input_title': 'Gear Type',
                        'input_message': '''Choose the gear used to retrieve the sample.
Listed at: https://github.com/SIOS-Svalbard/AeN_doc/blob/master/list_gear_types.csv''',
                        'error_title': 'Error',
                        'error_message': 'Not a valid gear type'
                    }
            },
    {'name': 'serialNumber',
                'disp_name': 'Serial Number',
                'description': 'The serial number of the instrument used',
                'format': 'text',
                'hstore': 'other',
                'valid': {
                    'validate': 'any',
                    'input_title': 'Instrument Serial Number',
                    'input_message': 'The serial number of the instrument used'
                }
                },

    # ==============================================================================
    # Other
    # ==============================================================================
    {'name': 'dataFilename',
                'disp_name': 'Data filename',
                'description': 'The name of the datafile',
                'format': 'text',
                'hstore': 'other',
                'valid': {
                    'validate': 'any',
                    'input_title': 'Data filename',
                    'input_message': 'The name of the datafile'
                }
                },

    # ==============================================================================
    # Comments
    # ==============================================================================
    {'name': 'comments1',
                'disp_name': 'Comments',
                'description': 'Main comments about the sample or event.',
                'width': 40,
                'format': 'text',
                'hstore': False,
                'valid': {
                         'validate': 'any',
                         'input_title': 'Comments',
                         'input_message': 'Main comments about the sample or event.'
                }
                },
    {'name': 'comments2',
                'disp_name': 'Comments #2',
                'description': 'Additional comments about the sample or event.',
                'width': 40,
                'format': 'text',
                'hstore': 'other',
                'valid': {
                         'validate': 'any',
                         'input_title': 'Comments #2',
                         'input_message': 'Additional comments about the sample or event.'
                }
                },
    {'name': 'comments3',
                'disp_name': 'Comments #3',
                'description': 'Additional comments about the sample or event.',
                'width': 40,
                'format': 'text',
                'hstore': 'other',
                'valid': {
                         'validate': 'any',
                         'input_title': 'Comments #3',
                         'input_message': 'Additional comments about the sample or event.'
                }
                },
    {'name': 'comments4',
                'disp_name': 'Comments #4',
                'description': 'Additional comments about the sample or event.',
                'width': 40,
                'format': 'text',
                'hstore': 'other',
                'valid': {
                         'validate': 'any',
                         'input_title': 'Comments #4',
                         'input_message': 'Additional comments about the sample or event.'
                }
                },
    {'name': 'comments5',
                'disp_name': 'Comments #5',
                'description': 'Additional comments about the sample or event.',
                'width': 40,
                'format': 'text',
                'hstore': 'other',
                'valid': {
                         'validate': 'any',
                         'input_title': 'Comments #5',
                         'input_message': 'Additional comments about the sample or event.'
                }
                },

    # ==============================================================================
    # History and modifications
    # ==============================================================================
    {'name': 'history',
                'disp_name': 'history',
                'description': 'Additional comments about the sample or event.',
                'width': 40,
                'format': 'text',
                'hstore': False,
                'valid': {
                         'validate': 'any',
                         'input_title': 'History',
                         'input_message': 'History of when the sample was first logged and the record updated.'
                }
                },
    {'name': 'created',
                'disp_name': 'created',
                'description': 'Timestamp when the sample was first logged.',
                'width': 40,
                'format': 'timestamp with time zone',
                'hstore': False,
                'valid': {
                         'validate': 'any',
                         'input_title': 'Created',
                         'input_message': 'Timestamp when the sample was first logged.'
                }
                },
    {'name': 'modified',
                'disp_name': 'modified',
                'description': 'Timestamp when the log of the sample was last modified.',
                'width': 40,
                'format': 'timestamp with time zone',
                'hstore': False,
                'valid': {
                         'validate': 'any',
                         'input_title': 'Modified',
                         'input_message': 'Timestamp when the log of the sample was last modified.'
                }
                },
    {'name': 'source',
                'disp_name': 'source',
                'description': 'Where the source was logged (file or page).',
                'width': 40,
                'format': 'text',
                'hstore': False,
                'valid': {
                         'validate': 'any',
                         'input_title': 'Source',
                         'input_message': 'Where the source was logged (file or page).'
                }
                },


    ]



# subsample_number = {'name': 'subsample_number',
#                     'disp_name': 'Number of subsamples',
#                     'format': 'int',
#                     'hstore': 'other',
#                     'valid': {
#                         'validate': 'integer',
#                         'criteria': '>',
#                         'value': 0,
#                         'input_title': 'Integer number of subsamples',
#                         'input_message': '''Integer > 0''',
#                         'error_title': 'Error',
#                         'error_message': 'Integer > 0'
#                     }
#                     }

# RETHINK THIS. MORE METADATA FROM ACDD CONVETIONS OR EML METADATA SO THE DATA ARE CLOSER TO BEING READY TO PUBLISH FOLLOWING THE CRUISE?
# BUT CAN'T BE TOO MUCH THAT IT WILL BE A LOT OF WORK
# IS PI_NAME REALLY NECCESSARY WHEN ALSO PROVIDED FOR EACH INDIVIDUAL SAMPLE? WHAT DOES THIS ADD?
# ==============================================================================
# For metadata fields
# ==============================================================================

# title = make_string_dict('title')
# title['valid']['input_message'] = 'A short descriptive title of the dataset'

# abstract = make_string_dict('abstract')
# abstract['valid'][
#     'input_message'] = '''An abstract providing context for the dataset.
# It should briefly explain the sampling and analysis procedures used to obtain the data.
# Here it is possible to refer to a published protocol'''

# pi_name = make_string_dict('pi_name')
# pi_name['disp_name'] = 'Principal investigator (PI)'

# pi_email = make_string_dict('pi_email')
# pi_email['disp_name'] = 'PI email'

# pi_institution = make_string_dict('pi_institution')
# pi_institution['disp_name'] = 'PI institution'

# pi_address = make_string_dict('pi_address')
# pi_address['disp_name'] = 'PI address'

# project_long = make_string_dict('project_long')
# project_long['disp_name'] = 'Project long name'

# project_short = make_string_dict('project_short')
# project_short['disp_name'] = 'Project short name'


# projectID = {'name': 'projectID',
#              'disp_name': 'Project ID',
#              'width': 40,
#              'valid': {
#                  'validate': 'any',
#                  'input_title': 'Project ID',
#                  'input_message': '''The project ID.
# For the Nansen Legacy this is:
# The Nansen Legacy (RCN # 276730)'''
#              }
#              }


# # List of all the available fields
# fields = [getattr(sys.modules[__name__], item) for item in dir() if not item.startswith(
#     "__") and isinstance(getattr(sys.modules[__name__], item), dict)]
