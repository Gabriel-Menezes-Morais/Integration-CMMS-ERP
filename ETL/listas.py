from ETL.monitor import check

def listagem_nec():
    df = check()

    return df['Cód. Interno'].drop_duplicates().tolist()

def listagem_ped(df_pedidos):

    if df_pedidos.empty:
        return []

    df_agg = df_pedidos.groupby('CodProCOPY', as_index=False)['Qtd'].sum()
    return df_agg.apply(lambda r: [r['CodProCOPY'], r['Qtd']], axis=1).tolist()