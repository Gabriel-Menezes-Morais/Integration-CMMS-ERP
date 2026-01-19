from ETL.Transformacao import df_transform
from database.funcoesBD import carrinho

#USAR AGENDADOR DE TAREFAS PARA ESTAR SEMPRE ATUALIZANDO A TABELA DA PÁGINA # CERTEZA?, n basta recarregar qnd abrir a página?

def check():

    df = df_transform() #tabela de produtos do CMMS
    df_pedidos = carrinho() #tabela de itens que foram necessitados do ERP
    
    df = df[df['Estoque'] < df['Estoque Mín.']]

    for id, linha in df.iterrows(): #Verifica se ja foi gerado necessidade do item 
        flag = 0 
        for id_pedidos, linha_pedidos in df_pedidos.iterrows():
            ref = linha['Cód. Interno'] #referência
            if ref == linha_pedidos['CodProCOPY']:
                flag += 1
                indice = df[df['Cód. Interno'] == ref].index
                df = df.drop(indice)
                continue

    print(df)
    return df
        
if __name__ == '__main__':
    check()