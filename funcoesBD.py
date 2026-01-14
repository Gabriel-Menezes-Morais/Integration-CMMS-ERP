import pandas as pd
from dotenv import load_dotenv
import os
import logging
import sqlalchemy
logger_Alerta = logging.getLogger("app")

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
        df = pd.read_sql(query, engine)
    except Exception as e:
        logger_Alerta.exception(f"Erro ao obter dados do carrinho: {e}")
        return None  # Retorna None ou uma lista vazia, dependendo do que faz sentido no seu contexto
    return df

def carrinho_full_filtrado():
    #Aqui, selecionamos os itens de necessidade que são somente da categoria de manutenção
    try:
        engine = conexao()  # Tenta estabelecer a conexão
        query = """SELECT *
                    From dbo.CadNecComCOPY AS E
                    INNER JOIN dbo.CadProCOPY AS P
                    ON E.CodProCOPY = P.REF
                    WHERE P.GrupoH = 3969"""
        df = pd.read_sql(query, engine)
    except Exception as e:
        logger_Alerta.exception(f"Erro ao obter dados filtrados do carrinho: {e}")
        return None  # Retorna None ou uma lista vazia
    return df

def deletar_item_carrinho(CODIGOS):
    # Deleta itens que foram necessitados e já estão na tabela dbo.CadNecComCOPY
    try:
        engine = conexao()  # Tenta estabelecer a conexão

        query = "DELETE FROM dbo.CadNecComCOPY WHERE CodProCOPY = :cod"

        parametros = [{"cod_id": item} for item in CODIGOS]

        with engine.begin() as conn:
            conn.execute(query, parametros)

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
            conn.execute(sql_insert, parametros)

    except Exception as e:
        logger_Alerta.exception(f"Erro ao adicionar itens ao carrinho: {e}")
        
    return