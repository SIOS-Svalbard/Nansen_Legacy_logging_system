#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 03 08:56:15 2022

@author: lukem
"""

from math import sin, cos, sqrt, atan2, radians

def distanceCoordinates(lat1,lon1,lat2, lon2):
    '''
    Calculates the distance between two decimal coordinates on earth based on the haversine equation for spherical trigonometry
    Parameters
    ----------
    lat1 : float
        Decimal latitude of 1st point
    lat2 : float
        Decimal latitude of 2nd point.
    lon1 : float
        Decimal longitude of 1st point
    lon2 : float
        Decimal longitude of 2nd point
    Returns
    -------
    Distance in kilometres
    '''
    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    # approximate radius of earth in km
    R = 6373.0

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c # distance in kilometres

    distance = round(distance,2)

    return distance

def split_personnel_list(personnel, df_personnel):
    '''
    personnel: list of personnel from html form input, in the format ['Joe Blogg (jblogg@emai.com)', 'Luke Marsden (lukem@unis.no)']
    df_personnel: pandas dataframe of the personnel from the personnel table in PSQL.

    returns pipe delimited string of personnel names, emails and institutions
    '''
    personnel_names_list = []
    personnel_emails_list = []
    personnel_orcids_list = []
    personnel_institutions_list = []

    if type(personnel) == str:
        if '|' in personnel:
            personnel = personnel.split(' | ')
        else:
            personnel = [personnel]

    if type(personnel) == float:
        personnel = []

    for person in personnel:
        if person != 'Choose...' and person != '' and type(person) == str:
            person_first_name = df_personnel.loc[df_personnel['personnel'] == person, 'first_name'].item()
            person_last_name = df_personnel.loc[df_personnel['personnel'] == person, 'last_name'].item()
            person_name = person_first_name + ' ' + person_last_name
            person_email = df_personnel.loc[df_personnel['personnel'] == person, 'email'].item()
            person_orcid = df_personnel.loc[df_personnel['personnel'] == person, 'orcid'].item()
            person_institution = df_personnel.loc[df_personnel['personnel'] == person, 'institution'].item()

            personnel_names_list.append(person_name)
            personnel_emails_list.append(person_email)
            personnel_orcids_list.append(person_orcid)
            personnel_institutions_list.append(person_institution)

    if type(personnel) == float:
        personnel_names = ''
        personnel_emails = ''
        personnel_orcids = ''
        personnel_institutions = ''
    else:
        personnel_names = " | ".join(personnel_names_list)
        personnel_emails = " | ".join(personnel_emails_list)
        personnel_orcids = " | ".join(personnel_orcids_list)
        personnel_institutions = " | ".join(personnel_institutions_list)

    return personnel_names, personnel_emails, personnel_orcids, personnel_institutions

def combine_personnel_details(names,emails):
    '''
    Combine personnel details from format stored in PSQL to format required for combined dropdown list

    Parameters
    ----------
    names : string
        Pipe-delimited list of names, e.g. 'Luke Marsden | John Doe'.
    emails : string
        Pipe-delimited list of emails, e.g. 'lukem@unis.no | johnd@unis.no'

    Returns
    -------
    personnel : list
        e.g. ['Luke Marsden (lukem@unis.no)', 'John Doe (johnd@unis.no)']

    '''

    try:
        names_list = names.split(' | ')
        emails_list = emails.split(' | ')
        personnel = [f"{name} ({email})" for (name, email) in zip(names_list, emails_list)]
    except:
        personnel = [None]

    return personnel


def get_title(series):
    type_ = series["sampletype"]
    if not type_:
        type_ = series["geartype"]
    human_readable = series["catalognumber"]
    if human_readable:
        return f"{human_readable} ({type_})"
    return type_


def format_form_value(field, value, format):
    if value == ['y']:
        if format in ['double precision', 'date', 'time']:
            return None
        else:
            return ''
    else:
        if len(value) == 1 and field not in ['pi_details', 'recordedBy']:
            return value[0]
        elif key in ['pi_details', 'recordedBy']:
            return value
        elif len(value) == 0:
            if format in ['double precision', 'date', 'time']:
                return None
            else:
                return ''
