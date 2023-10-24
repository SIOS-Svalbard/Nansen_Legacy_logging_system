import re

def add_one_to_numbers_in_string(string):
    # Regular expression pattern to match numbers in the string (including decimals)
    pattern = r'\b\d+(\.\d+)?\b'

    def increment_number(match):
        number = match.group()
        if '.' in number:
            return str(float(number) + 1)
        else:
            return str(int(number) + 1)

    # Use re.sub() with the replacement function to increment the numbers
    result = re.sub(pattern, increment_number, string)

    return result
