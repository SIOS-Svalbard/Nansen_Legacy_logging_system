def create_medium(uuid, text1, text2, text3, text4):
    """
    Creates the ZPL code for a medium label.
    Adds a text with the 8 first chracters from the uuid for ease of reading

    Parameters
    ----------
    uuid : str
        The 32 characters hex uuid

    text1 : str
        First line of text, limited to 18 characters

    text2 : str
        Second line of text, limited to 18 characters

    text3 : str
        Third line of text, limited to 18 characters

    text4 : str
        Fourth line of text, limited to 18 characters

    Returns
    ----------
    zpl : str
        The formatted ZPL code string that should be sent to the Zebra printer
    """

    # This uses a template made with ZebraDesigner, replacing the variables
    # with the necessary text {X}.
    zpl = '''
CT~~CD,~CC^~CT~
^XA~TA000~JSN^LT0^MNW^MTT^PON^PMN^LH0,0^JMA^PR4,4~SD30^JUS^LRN^CI28^XZ
^XA
^MMT
^PW898
^LL0295
^LS0
^BY110,110^FT506,111^BXN,4,200,22,22,1,~
^FH\^FD{0}^FS
^FT445,151^A0N,21,21^FH\^FD{1}^FS
^FT445,184^A0N,21,21^FH\^FD{2}^FS
^FT445,217^A0N,21,21^FH\^FD{3}^FS
^FT445,253^A0N,21,21^FH\^FD{4}^FS
^FT462,33^A0R,21,21^FH\^FD{5}^FS
^PQ1,0,1,Y^XZ'''.format(uuid,
        text1,
        text2,
        text3,
        text4,
        uuid[:8])

#    print(zpl)
    return zpl

def create_large(uuid, text1, text2, text3, text4,text5):
    """
    Creates the ZPL code for the large (25x51 mm) label.
    Adds a text with the 8 first characters from the uuid for ease of reading

    Parameters
    ----------
    uuid : str
        The 32 characters hex uuid

    text1 : str
        First line of text, limited to 20 characters

    text2 : str
        Second line of text, limited to 20 characters

    text3 : str
        Third line of text, limited to 20 characters

    text4 : str
        Fourth line of text, limited to 26 characters

    text5 : str
        Fifth line of text, limited to 26 characters

    Returns
    ----------
    zpl : str
        The formatted ZPL code string that should be sent to the Zebra printer
    """

    zpl= '''
CT~~CD,~CC^~CT~
^XA~TA000~JSN^LT0^MNW^MTT^PON^PMN^LH0,0^JMA^PR4,4~SD28^JUS^LRN^CI28^XZ
^XA
^MMT
^PW602
^LL0295
^LS0
^BY110,110^FT465,143^BXN,5,200,22,22,1,~
^FH\^FD{0}^FS
^FT491,171^A0N,21,21^FH\^FD{6}^FS
^FT35,67^A0N,42,40^FH\^FD{1}^FS
^FT35,119^A0N,42,40^FH\^FD{2}^FS
^FT35,171^A0N,42,40^FH\^FD{3}^FS
^FT35,226^A0N,42,40^FH\^FD{4}^FS
^FT35,278^A0N,42,40^FH\^FD{5}^FS
^PQ1,0,1,Y^XZ'''.format(uuid,
        text1,
        text2,
        text3,
        text4,
        text5,
        uuid[:8])

    return zpl
