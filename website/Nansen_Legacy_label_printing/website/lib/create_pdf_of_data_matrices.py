#!/usr/bin/python3
# encoding: utf-8
'''
 -- Creates pdf files for generating uuid labels

It defines classes_and_methods

'''

import sys
import math
import os
import qrcode
import uuid
import tempfile
from fpdf import FPDF

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2018-05-02'
__updated__ = '2019-08-03'

DEBUG = 0


def new_hex_uuid():
    """
    Generate a new hex UUID based on the host ID and time


    Returns
    ----------
    uuid : string
           uuid expressed as a hex value
    """
    return str(uuid.uuid1())  # Based on host ID and time


class QR(object):
    """
    QR class for holding the parameters needed to generate the QR code

    """

    def __init__(self):
        """
        Initialises the QR class
        """
        self.qr = qrcode.QRCode(
            version=3,  # 37 x 37 elements, 352 bits information
            # 15 % correction
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=9,  # px per box
            border=4,  # boxes for border (min is 4)
        )  # This gives a total size of 370 * 370 px

    def qr_image(self, uuid):
        """
        Creates a Pillow QR image of a given uuid

        Parameters
        ----------
        uuid : string
                The input string for the QR code

        Returns
        ----------
        img : Pillow image
                The QR code image
        """
        self.qr.clear()
        self.qr.add_data(uuid)
        self.qr.make(fit=False)
        return self.qr.make_image()


def dm_image(uuid, scale, dpi):
    """
    Creates a Pillow Data matrix image of a given uuid

    Parameters
    ----------
    uuid : string
            The input string for the 2D code

    Returns
    ----------
    img : Pillow image
            The Datamatrix code image
    """
    img = barcode('datamatrix', uuid, options=dict(format='square', version='22x22'),
                  data_mode='8bits', margin=0, scale=scale, dpi=dpi)
#     img.save("/export-b/work/Test.eps", "EPS")
    return img


class PDF(FPDF):

    def load_resource(self, reason, filename):
        return filename


def make_page(pdf, dpi, gearText, sampleText, M):
    """
    Makes an A4 page and fills it with QR codes

    Returns
    ----------
    page : Pillow image
            The A4 page image

    """

    inch = 25.4  # mm
    qr = QR()

# CDT
    # Margins
    top = 10
    side = 10

    # Spacing
    hpitch = 100
    vpitch = 21

    # number
    # print (M)
    if M > 12:
        cols = 2
    else:
        cols = 1
    full = math.floor(M/24)  # Number of full pages needed
    rows = full * 12
    if M-(rows*2) > 12:
        rows = rows+12
    else:
        rows = rows+(M-(rows*2))
    # print(rows,cols)

    # Padding for the QR
    pad = 5

    cell_size = 0.35   # mm
    # scale = cell_size / inch * dpi / 2 * 24 / 22
    # print("Scale", scale)
    # Make page
    pdf.set_font('Courier', 'B', 16)
    pdf.add_page()
#     page = Image.new('L', (int(width), int(height)), 'white')
#     font = ImageFont.truetype(
#         "/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf", 20)
#     draw = ImageDraw.Draw(page)

    def add_label(c, r, text, xshift, yshift):
        uuid = new_hex_uuid()
        fd, path = tempfile.mkstemp()
        # print(fd,path)
        try:
            with os.fdopen(fd, 'w') as tmp:
                # do stuff with temp file
                # print(uuid)
                img = qr.qr_image(uuid)
                img.save(path, format='PNG', resolution=dpi)
                pdf.image(
                    path, x=int(side + xshift + len(text)*4 + pad), y=int(top + yshift + pad), w=img.size[0] / inch, h=img.size[1] / inch, type='PNG')
                pdf.set_font('Courier', 'B', 16)
                pdf.text(
                    txt=text, x=int(side + xshift + pad), y=int(top + yshift + img.size[0]/2/inch + pad))
                pdf.set_font('Courier', 'B', 10)
                pdf.text(
                    txt=uuid[:8], x=int(side + xshift + len(text)*4), y=int(top + yshift + pad + img.size[0]/inch + 2))
        finally:
            os.remove(path)

    xshift = 0
    yshift = 0
    # Add top
    pdf.text(
        txt=gearText+" _____________", x=int(side + xshift + pad), y=int(top + yshift + pad))
    pdf.text(
        txt="Date _____________", x=int(side + xshift + pad), y=int(top + yshift + 3*pad))
    pdf.text(txt=new_hex_uuid()[:8], x=int(
        side + xshift + 100 + pad), y=int(top + yshift + pad))

    yshift = yshift + vpitch
    ii = 0
    kk = 0
    for r in range(rows):  # Loop over the rows
        # print(xshift,yshift)
        if r != 0 and r % 12 == 0:
            pdf.add_page()
            xshift = 0
            yshift = 0
            ii = ii+12
            if M-kk < 12:  # Check how many columns we need
                cols = 1

        xshift = 0
        for c in range(cols):  # Loop over the columns
            # if (c == cols-1 and r == rows-1):
                #print(c, r, "Breaking")
                # break

            jj = ii + (c*12)
            # print(ii, c, jj, r, rows)
            if jj > M:
                continue

            text = sampleText+" #" + format(jj+1, "02d")
            add_label(c, r, text, xshift, yshift)
            kk = kk+1

            xshift = xshift + hpitch
        yshift = yshift + vpitch
        ii = ii+1


def save_pages(url, gearText="CTD", sampleText="Niskin", M=24, N=1):
    """
    Saves multiple pages of QR codes to a pdf file

    Parameters
    ----------

    url : string
        The output file

    N : int
        The number of pages wanted
        Default :1

    """
#     pages = []
    dpi = 600
    pdf = PDF('P', 'mm', 'A4')
#     first = make_page(dpi)
#     if N > 1:
    for ii in range(N):
        make_page(pdf, dpi, gearText, sampleText, M)

    pdf.output(url, 'F')


def main(argv=None):  # IGNORE:C0111
    '''Command line options.'''

    try:
        args = parse_options()
        output = args.output
        save_pages(output+'.pdf', N=args.n, gearText=args.gear,
                   sampleText=args.sample, M=args.m)
        return 0
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

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    # Setup argument parser
    parser = ArgumentParser(description=program_license,
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('output', help='''The output file''')
    parser.add_argument("-v", "--verbose", dest="verbose", action="count", default=0,
                        help="set verbosity level [default: %(default)s]")
    parser.add_argument('-V', '--version', action='version',
                        version=program_version_message)
    parser.add_argument(
        '-n', dest='n', default=1, type=int, help="Set the number of pages wanted, [default: %(default)s]")
    parser.add_argument(
        '--gear', dest='gear', default="CTD", type=str, help="Set the gear type, [default: %(default)s]")
    parser.add_argument(
        '--sample', dest='sample', default="Niskin", type=str, help="Set the sample type, [default: %(default)s]")
    parser.add_argument(
        '-m', dest='m', default=24, type=int, help="Set the number of samples, [default: %(default)s]")

    # Process arguments
    args = parser.parse_args()

    if args.verbose > 0:
        print("Verbose mode on")

    return args


if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-v")
    sys.exit(main())
