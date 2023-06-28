import xlsxwriter
from argparse import Namespace
import os.path
from website import DB
from website.lib.get_data import get_institutions_list

DEFAULT_FONT = 'Calibri'
DEFAULT_SIZE = 10

class Template(object):
    """
    Spreadsheet template object
    """

    def __init__(self, filepath):
        self.filepath = filepath
        self.workbook = xlsxwriter.Workbook(self.filepath)

        # Set font
        self.workbook.formats[0].set_font_name(DEFAULT_FONT)
        self.workbook.formats[0].set_font_size(DEFAULT_SIZE)

    def add_variables_sheet(self):
        self.variables_sheet = Variables_sheet(self)

    def add_personnel_sheet(self, sheetname):
        sheet = Personnel_sheet(sheetname, self)
        sheet.write_content()

    def close_and_save(self):
        self.workbook.close()

class Variables_sheet(object):
    """
    For options that go in drop-down lists
    This will be hidden
    """
    def __init__(self, template):
        self.template = template
        self.sheetname = 'Variables'
        self.sheet = template.workbook.add_worksheet(self.sheetname)
        self.sheet.hide()

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

        self.sheet.write(0, 0, variable)
        name = 'Table_' + variable.replace(' ', '_').capitalize()

        self.sheet.add_table(
            1, 0,
            1 + len(parameter_list), 0,
            {'name': name,
                'header_row': 0}
        )

        for ii, par in enumerate(sorted(parameter_list, key=str.lower)):
            self.sheet.write(1 + ii, 0, par)
        ref = '=INDIRECT("' + name + '")'

        return ref

class Personnel_sheet(object):
    """
    Personnel sheet object
    """
    def __init__(self, sheetname, template):
        self.sheetname = sheetname
        self.template = template
        self.sheet = self.template.workbook.add_worksheet(self.sheetname)

        self.header_format = self.template.workbook.add_format({
            'font_name': DEFAULT_FONT,
            'bottom': True,
            'right': True,
            'bold': False,
            'text_wrap': True,
            'valign': 'vcenter',
            'font_size': DEFAULT_SIZE + 1,
            'bg_color': '#C0DF85'
        })

    def write_content(self):
        '''
        Writing one column for each field
        '''
        header_row = 4
        start_row = header_row + 2
        parameter_row = header_row + 1  # Parameter row, hidden
        end_row = start_row + 1000  # final row to extend formatting and cell restrictions to

        self.sheet.merge_range(
            'A2:F2',
            'Use this template to register all personnel that you will use in the logging system.'
            )
        self.sheet.merge_range(
            'A3:F3',
            'Include anyone you will refer to as a cruise leader, PI, or the person who is logging a record in the logging system'
            )

        # Write title row
        self.sheet.write(header_row, 0, 'First name', self.header_format)
        self.sheet.write(header_row, 1, 'Last name', self.header_format)
        self.sheet.write(header_row, 2, 'Email address', self.header_format)
        self.sheet.write(header_row, 3, 'OrcID', self.header_format)
        self.sheet.write(header_row, 4, 'Instituion', self.header_format)
        self.sheet.write(header_row, 5, 'Instituion if not in drop-down list (column E)', self.header_format)

        # Write row below with parameter name
        self.sheet.write(parameter_row, 0, 'firstName', self.header_format)
        self.sheet.write(parameter_row, 1, 'lastName', self.header_format)
        self.sheet.write(parameter_row, 2, 'email', self.header_format)
        self.sheet.write(parameter_row, 3, 'orcID', self.header_format)
        self.sheet.write(parameter_row, 4, 'instituion', self.header_format)
        self.sheet.write(parameter_row, 5, 'instituionToRegister', self.header_format)

        institutions_list = sorted(get_institutions_list(DB)) + ['Other']

        validation_orcid = {
            "validate": "any",
            "input_title": "OrcID",
            "input_message": "Your OrcID.\n\rThis stays constant if other details change.\n\re.g. https://orcid.org/0000-0002-9746-544X  ",
        }

        self.sheet.data_validation(first_row=start_row,
                                   first_col=3,
                                   last_row=end_row,
                                   last_col=3,
                                   options=validation_orcid)

        validation_institution = {
            "validate": "list",
            "input_title": "Institution",
            "input_message": "Choose institution from drop-down list.\n\rIf your institution is not included, select 'Other'  \n\rand write your institution in column F",
            "error_title": "Error",
            "error_message": "Not a valid value, pick a value from the drop-down list."
        }

        ref = self.template.variables_sheet.add_row(
            'institution', institutions_list
            )

        validation_institution['value'] = ref

        self.sheet.data_validation(first_row=start_row,
                                   first_col=4,
                                   last_row=end_row,
                                   last_col=4,
                                   options=validation_institution)

        validation_other_institutions = {
            "validate": "any",
            "input_title": "Other Institutions",
            "input_message": "Full name of you institution\n\rOnly fill this in if you haven't selected  \n\ryour institution in column E",
        }

        self.sheet.data_validation(first_row=start_row,
                                   first_col=5,
                                   last_row=end_row,
                                   last_col=5,
                                   options=validation_other_institutions)

        # Set height of row
        self.sheet.set_row(header_row, height=45)
        self.sheet.set_column(0,100,20)

        # Freeze the rows at the top
        self.sheet.freeze_panes(start_row, 0)

        # Hide ID row
        self.sheet.set_row(parameter_row, None, None, {'hidden': True})

        self.sheet.activate()

def create_personnel_template(filepath):
    """
    Method for calling from other python programs
    Parameters
    ----------
    filepath: string
        The output file
    """

    args = Namespace()
    args.verbose = 0
    args.dir = os.path.dirname(filepath)
    args.filepath = filepath

    template = Template(args.filepath)
    template.add_variables_sheet()
    template.add_personnel_sheet('Personnel')
    template.close_and_save()
