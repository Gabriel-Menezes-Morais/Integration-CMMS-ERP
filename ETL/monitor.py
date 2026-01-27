from ETL.Transformacao import df_transform
from database.funcoesBD import carrinho

def check():

    df = df_transform()  # tabela de produtos do CMMS
    df_pedidos = carrinho()  # tabela de itens que foram necessitados (APENAS PENDENTES)
    
    # Filtra itens abaixo do estoque mínimo
    df = df[df['Estoque'] < df['Estoque Mín.']]

    # NOVA LÓGICA: Considera a quantidade já pedida pendente
    if df_pedidos is not None and not df_pedidos.empty:
        # Agrupa por código e soma as quantidades pedidas pendentes
        qtd_pedida = df_pedidos.groupby('CodProCOPY')['Qtd'].sum().to_dict()
        
        # Calcula estoque projetado (estoque atual + pedidos pendentes)
        df['Estoque_Projetado'] = df.apply(
            lambda row: row['Estoque'] + qtd_pedida.get(row['Cód. Interno'], 0),
            axis=1
        )
        
        # Remove apenas os itens cujo estoque projetado já atinge o mínimo
        df = df[df['Estoque_Projetado'] < df['Estoque Mín.']]
        
        # Remove a coluna auxiliar
        df = df.drop(columns=['Estoque_Projetado'])

        # remove duplicados, mantendo o primeiro
        df = df.drop_duplicates(subset=['Cód. Interno'], keep='first')
    print(df)
    return df

if __name__ == '__main__':
    check()