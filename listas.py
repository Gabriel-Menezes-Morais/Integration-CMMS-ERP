from monitor import check

def listagem_nec():
    df = check()
    # Return only unique internal codes to avoid duplicate items in the UI
    return df['Cód. Interno'].drop_duplicates().tolist()

def listagem_ped(df_pedidos):
    # Aggregate by product code so each product appears only once (sum quantities)
    if df_pedidos.empty:
        return []

    df_agg = df_pedidos.groupby('CodProCOPY', as_index=False)['Qtd'].sum()
    return df_agg.apply(lambda r: [r['CodProCOPY'], r['Qtd']], axis=1).tolist()