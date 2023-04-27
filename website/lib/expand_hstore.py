import numpy as np

def expand_hstore(df):
    '''
    Expandas the hstore column named 'other'
    Dumps data contained within to individual columns
    '''

    # Creating new columns from the hstore key/value pairs in the 'other' column
    newdf = df.join(df['other'].str.extractall(r'\"(.+?)\"=>\"(.+?)\"')
         .reset_index()
         .pivot(index=['level_0', 'match'], columns=0, values=1)
         .groupby(level=0)
         .agg(lambda x: ''.join(x.dropna()))
         .replace('', np.nan)
         )

    return newdf
