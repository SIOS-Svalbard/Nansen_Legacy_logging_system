#!/usr/bin/env python3
# encoding: utf-8
'''
 -- Creates and prints circular 12.7 mm labels for AeN

 This program enables the creation and printing of labels of the 10 mm 
 circular type

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.


@author:     Pål Ellingsen

@copyright:  2018-2019 UNIS. 


@contact:    pale@unis.no
@deffield    updated: Updated
'''

import sys
import os
import time
import uuid
import warnings
import socket
import datetime as dt

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2018-07-03'
__updated__ = '2019-05-15'

DEBUG = 1


def create_label():
    """
    Creates the ZPL code for the label with 3 uuids.
----------
    zpl : str
        The formatted ZPL code string that should be sent to the Zebra printer 
    """
    uuids = []
    for i in range(3):
        uuids.append(str(uuid.uuid1()))
        # Ensure that we are not generating them to fast
        time.sleep(1. / 1e6)  # 1 us

    # 3 UUIDS
    zpl = '''
CT~~CD,~CC^~CT~
^XA~TA000~JSN^LT0^MNW^MTT^PON^PMN^LH0,0^JMA^PR4,4~SD28^JUS^LRN^CI0^XZ
^XA
^MMT
^PW570
^LL0150
^LS0
^BY88,88^FT148,65^BXI,4,200,22,22,1,~
^FH\^FD{0}^FS
^BY88,88^FT328,65^BXI,4,200,22,22,1,~
^FH\^FD{1}^FS
^BY88,88^FT508,65^BXI,4,200,22,22,1,~
^FH\^FD{2}^FS
^PQ1,0,1,Y^XZ'''.format(uuids[0],
                        uuids[1],
                        uuids[2])

    # 4 UUIDS
    # zpl = '''
# CT~~CD,~CC^~CT~
# ^XA~TA000~JSN^LT0^MNW^MTT^PON^PMN^LH0,0^JMA^PR4,4~SD24^JUS^LRN^CI0^XZ
# ^XA
# ^MMT
# ^PW650
# ^LL0100
# ^LS0
# ^BY88,88^FT60,119^BXN,3,200,22,22,1,~
# ^FH\^FD{0}^FS
# ^BY88,88^FT214,119^BXN,3,200,22,22,1,~
# ^FH\^FD{1}^FS
# ^BY88,88^FT368,119^BXN,3,200,22,22,1,~
# ^FH\^FD{2}^FS
# ^BY88,88^FT521,119^BXN,3,200,22,22,1,~
# ^FH\^FD{3}^FS
# ^PQ1,0,1,Y^XZ'''.format(uuids[0], uuids[1], uuids[2], uuids[3])

    del uuids

    return zpl


def print_labels(args):
    '''
    Prints N number of labels. N will be rounded up to the nearest multiple of 3


    Parameters
    ----------
    args : ArgumentParser args
           This should contain:
             the ip (args.ip) 
             the number of labels (args.N) 

    '''

    PORT = 9100
    BUFFER_SIZE = 1024
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((args.ip, PORT))

    for ii in range(args.N // 3):
        zpl = create_label()
        if args.verbose > 0:
            print(zpl)

        sock.send(bytes(zpl, "utf-8"))

    sock.close()


def main(argv=None):  # IGNORE:C0111
    '''Command line options.'''

    try:
        args = parse_options()
        print_labels(args)
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0


def parse_options():
    """
    Parse the command line options and return these. Also performs some basic
    sanity checks, like checking number of arguments.
    """
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (
        program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by Pål Ellingsen on %s.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

    USAGE
    ''' % (program_shortdesc, str(__date__))

    # Setup argument parser
    parser = ArgumentParser(description=program_license,
                            formatter_class=RawDescriptionHelpFormatter)
#     parser.add_argument('output', help='''The output file''')
    parser.add_argument("-v", "--verbose", dest="verbose", action="count", default=0,
                        help="set verbosity level [default: %(default)s]")
    parser.add_argument('-V', '--version', action='version',
                        version=program_version_message)
    parser.add_argument('N', type=int, help='''Set the number of labels to be printed,
if not a multiple of 3 will be rounded up to a multiple of 3''')
    parser.add_argument('ip',  type=str,
                        help="Set the IP of the printer, format is '192.168.1.1'")

    # Process arguments
    args = parser.parse_args()

    # Round up to nearest multiple of 3
    args.N = args.N + (args.N % 3)
    if args.verbose > 0:
        print("Verbose mode on")

    return args


if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-v")
    sys.exit(main())
