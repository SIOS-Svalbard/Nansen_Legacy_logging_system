#!/usr/bin/python3
# encoding: utf-8


'''
 -- Web interface for generating an UUID.


@author:     Pål Ellingsen
@deffield    updated: Updated
'''


import os
import time
import sys
import cgi
import cgitb
import codecs
import uuid
import shutil
import textwrap
import tempfile

__updated__ = '2018-06-29'


cgitb.enable()

def uuids_many(path, number=100):
    '''
    Creates a file with n uuids, one per line
    '''
    f = open(path,"w")
    for n in range(number):
        f.write(str(uuid.uuid1())+'\n')

def warn(message, color='red'):
    message = bytes(message, "utf-8")
    sys.stdout.buffer.write(b'<p style="color:'+bytes(color,"utf-8")+b'">'+message+b'</p>')

method = os.environ.get("REQUEST_METHOD", "GET")

from mako.template import Template
from mako.lookup import TemplateLookup

templates = TemplateLookup(
    directories=['templates'], output_encoding='utf-8')

if method == "GET":  # This is for getting the page

    # Using sys, as print doesn't work for cgi in python3
    template = templates.get_template("uuid.html")

    sys.stdout.flush()
    sys.stdout.buffer.write(b"Content-Type: text/html\n\n")
    sys.stdout.buffer.write(
        template.render(uuid=uuid))

elif method == "POST":
    
    form = cgi.FieldStorage()

    if "file" in form:
        tmpfile = '/tmp/tmpfile.txt'
        try:
            number = int(form["number"].value)
        except:
            number = 0
        
        if number < 1:
            error = "Please enter an integer greater than 0"
            sys.stdout.flush()
            sys.stdout.buffer.write(b"Content-Type: text/html\n\n")
            sys.stdout.buffer.write(b"<!doctype html>\n<html>\n <meta charset='utf-8'>")
            warn(error)
            sys.stdout.buffer.write(b'</html>')
        else:

            filename='uuids.txt'
            print("Content-Type: text/plain")
            print("Content-Disposition: attachment; filename="+filename+"\n")
            path = "/tmp/" + next(tempfile._get_candidate_names()) + ".txt"

            uuids_many(path, number)

            with open(path, "rb") as f:
                sys.stdout.flush()
                shutil.copyfileobj(f, sys.stdout.buffer)
    else:
        template = templates.get_template("uuid.html")

        sys.stdout.flush()
        sys.stdout.buffer.write(b"Content-Type: text/html\n\n")
        sys.stdout.buffer.write(
            template.render(uuid=uuid))
