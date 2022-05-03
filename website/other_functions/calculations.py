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
