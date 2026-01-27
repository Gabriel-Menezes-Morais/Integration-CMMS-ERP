import pandas as pd
from dotenv import load_dotenv
import os
import logging
import sqlalchemy
import time
import datetime
logger_Alerta = logging.getLogger("app")
from sqlalchemy import text
# Carrega o arquivo .env
load_dotenv()

server = os.getenv("DB_SERVER")
database = os.getenv("DB_NAME")
uid = os.getenv("DB_UID")
pwd = os.getenv("DB_PWD")

dados_conexao = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server={server};"
        f"Database={database};"
        f"UID={uid};"
        f"PWD={pwd};"
        "TrustServerCertificate=yes;"
)

def conexao():
    
    #Cria e retorna uma conexão nova com o SQL Server
    try:
        engine = sqlalchemy.create_engine(f"mssql+pyodbc:///?odbc_connect={dados_conexao}", fast_executemany=True)
    except Exception as e:
        logger_Alerta.exception(f"Erro ao conectar ao banco de dados: {e}")
        raise e
    return engine

def carrinho():
    #Verifica e armazena em df os itens que estão na tabela de Carrinho, i.e., os quais passaram pela geração de necessidades
    try:
        engine = conexao()  # Tenta estabelecer a conexão
        query = "SELECT * FROM dbo.CadNecComCOPY WHERE IDPedCom IS NULL"
        df = pd.read_sql(text(query), engine)
    except Exception as e:
        logger_Alerta.exception(f"Erro ao obter dados do carrinho: {e}")
        return None  # Retorna None ou uma lista vazia, dependendo do que faz sentido no seu contexto
    return df

def carrinho_full_filtrado():
    #Aqui, selecionamos os itens de necessidade que são somente da categoria de manutenção
    try:
        engine = conexao()  # Tenta estabelecer a conexão
        query = """SELECT DISTINCT E.*
                    From dbo.CadNecComCOPY AS E
                    INNER JOIN dbo.CadProCOPY AS P
                    ON E.CodProCOPY = P.REF
                    WHERE P.GrupoH = 3969
                    ORDER BY E.CodProCOPY"""
        df = pd.read_sql(text(query), engine)
    except Exception as e:
        logger_Alerta.exception(f"Erro ao obter dados filtrados do carrinho: {e}")
        return None  # Retorna None ou uma lista vazia
    return df

def deletar_item_carrinho(CODIGOS):
    # Deleta itens que foram necessitados e já estão na tabela dbo.CadNecComCOPY
    try:
        engine = conexao()  # Tenta estabelecer a conexão

        query = "DELETE FROM dbo.CadNecComCOPY WHERE CodProCOPY = :cod"

        parametros = [{"cod": item} for item in CODIGOS]

        with engine.begin() as conn:
            conn.execute(text(query), parametros)

    except Exception as e:
        logger_Alerta.exception(f"Erro ao deletar itens do carrinho: {e}")
    return

def compra_item(datas):
    # Adiciona itens selecionados na tabela carrinho
    try:
        engine = conexao()  # Tenta estabelecer a conexão

        sql_insert = "INSERT INTO dbo.CadNecComCOPY (CodProCOPY, Qtd) VALUES (:cod, :qtd)"

        parametros = [{"cod": item[0], "qtd": item[1]} for item in datas]

        with engine.begin() as conn:
            conn.execute(text(sql_insert), parametros)

    except Exception as e:
        logger_Alerta.exception(f"Erro ao adicionar itens ao carrinho: {e}")
        
    return

def CadastrarBD(Item_Cadastro):
    # Função de cadastro de item no banco de dados via stored procedure
    try:
        engine = conexao()  # Tenta estabelecer a conexão

        sql_sp = "INSERT INTO dbo.CadProCOPY (REF, DESCRICAO, UNIDADE) VALUES (:cod_interno, :descricao, :unidade)"

        parametros = {
            "cod_interno": Item_Cadastro["codigo"],
            "descricao": Item_Cadastro["descricao"],
            "unidade": Item_Cadastro["unidade"]
        }

        with engine.begin() as conn:
            conn.execute(text(sql_sp), parametros)

    except Exception as e:
        logger_Alerta.exception(f"Erro ao cadastrar item no banco de dados: {e}")
        
    return

def marcar_como_recebido(CODIGO):
    """Marca o item como recebido atualizando a Data_Recebimento"""
    try:
        engine = conexao()
        data_recebimento = datetime.datetime.now()
        
        query = """UPDATE dbo.CadNecComCOPY 
                   SET Data_Recebimento = :data 
                   WHERE CodProCOPY = :cod 
                   AND IDPedCom IS NOT NULL 
                   AND Data_Recebimento IS NULL"""
        
        with engine.begin() as conn:
            conn.execute(text(query), {"data": data_recebimento, "cod": CODIGO})
        
        logger_Alerta.info(f"Item {CODIGO} marcado como recebido em {data_recebimento.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        logger_Alerta.exception(f"Erro ao marcar item como recebido: {e}")
    return

if __name__ == "__main__":
    # Teste rápido das funções
    df_carrinho = carrinho_full_filtrado()
    print(df_carrinho.head())