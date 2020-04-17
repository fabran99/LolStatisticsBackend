import pandas as pd
import numpy as np

def monary_array_to_df(arrays, columns):
    y = np.array(np.ma.array(arrays, fill_value=np.nan).filled(), dtype=object)

    df = pd.DataFrame(y.T, columns=[x['name'] for x in columns])
    for x in columns:
        if x['name'] == "_id":
           df[x['name']]=df[x['name']].apply(lambda y: y.hex()) 
           continue

        df[x['name']]=df[x['name']].apply(lambda y:x['function'](y))
    return df

