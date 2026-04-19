import pandas as pd

def preparar_dados(df):
    if df.empty:
        return df
    df['data'] = pd.to_datetime(df['data'])
    return df
