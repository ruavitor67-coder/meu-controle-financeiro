import pandas as pd

def preparar_dados(df):
    if df.empty:
        return df
    df['data'] = pd.to_datetime(df['data'])
    return df

def resumo_mensal(df):
    return df.groupby(df['data'].dt.to_period('M'))['valor'].sum()
