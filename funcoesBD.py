import pyodbc #MUDAR DEPOIS PARA SQLALCHEMY
import pandas as pd
from dotenv import load_dotenv
import os
import logging

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
        conn = pyodbc.connect(dados_conexao)
    except Exception as e:
        logger_Alerta.exception(f"Erro ao conectar ao banco de dados: {e}")
        raise e
    return conn

def carrinho():
    #Verifica e armazena em df os itens que estão na tabela de Carrinho, i.e., os quais passaram pela geração de necessidades
    try:
        conn = conexao()  # Tenta estabelecer a conexão
        query = "SELECT * FROM dbo.CadNecComCOPY WHERE IDPedCom IS NULL"
        df = pd.read_sql(query, conn)
    except Exception as e:
        logger_Alerta.exception(f"Erro ao obter dados do carrinho: {e}")
        return None  # Retorna None ou uma lista vazia, dependendo do que faz sentido no seu contexto
    finally:
        if 'conn' in locals():  # Verifica se a conexão foi criada
            conn.close()  # Garante que a conexão seja fechada
    return df

def carrinho_full_filtrado():
    #Aqui, selecionamos os itens de necessidade que são somente da categoria de manutenção
    try:
        conn = conexao()  # Tenta estabelecer a conexão
        query = """SELECT *
                    From dbo.CadNecComCOPY AS E
                    INNER JOIN dbo.CadProCOPY AS P
                    ON E.CodProCOPY = P.REF
                    WHERE P.GrupoH = 3969"""
        df = pd.read_sql(query, conn)
    except Exception as e:
        logger_Alerta.exception(f"Erro ao obter dados filtrados do carrinho: {e}")
        return None  # Retorna None ou uma lista vazia
    finally:
        if 'conn' in locals():
            conn.close()  # Garante que a conexão seja fechada
    return df

def deletar_item_carrinho(CODIGOS):
    # Deleta itens que foram necessitados e já estão na tabela dbo.CadNecComCOPY
    try:
        conn = conexao()  # Tenta estabelecer a conexão
        cursor = conn.cursor()

        # Use = ? e executemany com um parâmetro por execução para evitar problemas com IN (?)
        query = "DELETE FROM dbo.CadNecComCOPY WHERE CodProCOPY = ?"

        for i in range(len(CODIGOS)):
            CODIGOS[i] = [CODIGOS[i]]

        cursor.executemany(query, CODIGOS)

        conn.commit()
    except Exception as e:
        logger_Alerta.exception(f"Erro ao deletar itens do carrinho: {e}")
    finally:
        cursor.close()
        if 'conn' in locals():
            conn.close()  # Garante que a conexão seja fechada
    return

def compra_item(datas):
    # Adiciona itens selecionados na tabela carrinho
    try:
        conn = conexao()  # Tenta estabelecer a conexão
        cursor = conn.cursor()

        sql_insert = "INSERT INTO dbo.CadNecComCOPY (CodProCOPY, Qtd) VALUES (?, ?)"
        cursor.executemany(sql_insert, datas)

        conn.commit()
    except Exception as e:
        logger_Alerta.exception(f"Erro ao adicionar itens ao carrinho: {e}")
    finally:
        cursor.close()
        if 'conn' in locals():
            conn.close()  # Garante que a conexão seja fechada
    return