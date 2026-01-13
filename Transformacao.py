from integracao import extract
import pandas as pd
import logging

logger_SIMPLES = logging.getLogger("app.lowlevel")
logger_ALERTA = logging.getLogger("app")

def df_transform():
    #transformando os dados para serem usados posteriormente no SQL Server
    try:
        df = extract()
    except Exception as e:
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de falha na extração
    try:
        #Colunas numéricas do dataframe
        cols_num = ['Entradas', 'Saidas', 'Qut Encomendada', 'Qut Reservada (OS)', 'Estoque Mín.', 'Estoque', 'Saldo']

        for col in cols_num:
            df[col] = df[col].astype(str).str.replace('.', '', regex=False) #Retira ponto do milhar
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False) #Troca virgula por ponto
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        #colunas financeiras
        cols_fin = ['Custo Médio', 'Valor do Estoque']
        for col in cols_fin:
            df[col] = df[col].astype(str).str.replace('R$', '', regex=False) #Retira símbolos desnecessário
            df[col] = df[col].astype(str).str.replace('.', '', regex=False)
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df['Ativo'] = df['Ativo'].apply(lambda x: 1 if str(x).lower() in ['sim', 'true', 's', '1'] else 0)

        logger_SIMPLES.info(f"Extração bem-sucedida - linhas: {df.shape[0]} colunas: {df.shape[1]}")
        return df
    except Exception as e:
        logger_ALERTA.exception(f"Erro na transformação dos dados: {e}")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro

if __name__ =="__main__":
    df = df_transform()
    print(df.info())