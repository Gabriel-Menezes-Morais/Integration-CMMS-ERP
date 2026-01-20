from ETL.Transformacao import df_transform
from database.funcoesBD import carrinho

#USAR AGENDADOR DE TAREFAS PARA ESTAR SEMPRE ATUALIZANDO A TABELA DA PÁGINA # CERTEZA?, n basta recarregar qnd abrir a página?

def check():

    df = df_transform() #tabela de produtos do CMMS
    df_pedidos = carrinho() #tabela de itens que foram necessitados do ERP
    
    df = df[df['Estoque'] < df['Estoque Mín.']]

    # Optimized: use isin instead of nested loops
    df = df[~df['Cód. Interno'].isin(df_pedidos['CodProCOPY'])]

    print(df)
    return df
        
if __name__ == '__main__':
    check()