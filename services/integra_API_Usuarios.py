import requests
from requests import Request, Session   
import pandas as pd
import os
import logging
from dotenv import load_dotenv
import json
from logging.config import dictConfig
import time

with open("config/log_config.json", "r") as f:
    configLOG = json.load(f)

logging.config.dictConfig(configLOG)

# Valida configurações mínimas
logger_ALERTA = logging.getLogger("app")
logger_SIMPLES = logging.getLogger("app.lowlevel")
# Carrega o arquivo .env
load_dotenv()

def _create_session_with_retries(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
    """Cria uma Session do requests com política de retry para falhas transitórias."""
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    session = Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def cadastrar_aut():

    url = os.getenv("ENDPOINT_AUTENTICACAO")
    TOKEN = os.getenv("TOKEN_AUTENTICACAO")

    if not url:
        logger_ALERTA.error("ENDPOINT não definido nas variáveis de ambiente.")
        raise ValueError("ENDPOINT não definido")

    if not TOKEN:
        logger_ALERTA.error("TOKEN não definido nas variáveis de ambiente.")
        raise ValueError("TOKEN não definido")

    payload = {
        "token": os.getenv("TOKEN_AUTENTICACAO"),
        "checklists": [
            {
                "nome": "Teste Checklist API 2",
                "rev": "1",
                "itens": [
                    {"descricao": "Grupo 1", "tipo": "split", "medicao": "", "pendencia": 1, "foto": 0},
                    {"descricao": "Item 1", "tipo": "item", "medicao": "", "pendencia": 1, "foto": 0},
                    {"descricao": "Item 2", "tipo": "item", "medicao": "Horímetro (h)", "pendencia": 1, "foto": 0}
                ]
            },
            {
                "nome": "Teste Checklist API 3",
                "rev": "1",
                "itens": [
                    {"descricao": "Grupo 1", "tipo": "split", "medicao": "", "pendencia": 1, "foto": 0},
                    {"descricao": "Item 1", "tipo": "item", "medicao": "", "pendencia": 1, "foto": 1},
                    {"descricao": "Item 2", "tipo": "item", "medicao": "Horímetro (h)", "pendencia": 1, "foto": 1}
                ]
            }
        ]
    }
    
    headers = {"Content-Type": "application/json"}

    s = _create_session_with_retries()

    try:
        prepped = Request('POST', url, json=payload, headers=headers).prepare()
        response = s.send(prepped, timeout=10)

        # Lança exceção para status codes 4xx/5xx
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as e:
            logger_ALERTA.exception("Erro ao decodificar JSON da resposta: %s", e)
            return pd.DataFrame()

        df = pd.DataFrame(data)
        
        print(40 * "-" + "SUCESSO" + 40 * "-")
        print("STATUS CODE: {}".format(response.status_code))
        print(90 * "-")
        print(df.info())
        print(df)
        print(90 * "-")
        print(df.columns)
        print(90 * "-")

        return df

    except requests.exceptions.Timeout as e:
        logger_ALERTA.exception("Timeout ao chamar a API: %s", e)
        return pd.DataFrame()
    except requests.exceptions.ConnectionError as e:
        logger_ALERTA.exception("Erro de conexão com a API: %s", e)
        return pd.DataFrame()
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', 'desconhecido')
        logger_ALERTA.exception("Resposta HTTP inválida: %s - status: %s", e, status)
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        logger_ALERTA.exception("Erro não esperado ao chamar a API: %s", e)
        return pd.DataFrame()
    finally:
        try:
            s.close()
        except Exception:
            pass

def edit_movest(ID, CODIGO, QTD):

    url_mov = os.getenv("ENDPOINT_MOV")
    token_mov = os.getenv("TOKEN_MOV")

    if not url_mov:
        logger_ALERTA.error("ENDPOINT não definido nas variáveis de ambiente.")
        raise ValueError("ENDPOINT não definido")

    if not token_mov:
        logger_ALERTA.error("TOKEN não definido nas variáveis de ambiente.")
        raise ValueError("TOKEN não definido")
    
    named_tuple = time.localtime()
    time_string = time.strftime("%Y-%m-%d %H:%M", named_tuple)
    
    payload = { 
        "token": token_mov,
        "id": ID,
        "data_recebido": time_string,
        "materiais": [
            {
                "codigo": CODIGO,
                "qut": QTD,
                "acao": "edit"
            }
        ]
    }
    headers = {}

    s = _create_session_with_retries()

    try:
        prepped = Request('POST', url_mov, json=payload, headers=headers).prepare()
        response = s.send(prepped, timeout=10)
        response.raise_for_status()

        try:
            status = response.json()
        except ValueError as e:
            logger_ALERTA.exception("Erro ao decodificar JSON da resposta: %s", e)
            return

        logger_SIMPLES.info(status)
        logger_SIMPLES.info(response.status_code)
        
        # Atualiza o banco local com a data de recebimento
        from database.funcoesBD import marcar_como_recebido
        marcar_como_recebido(CODIGO)
        
        return

    except requests.exceptions.Timeout as e:
        logger_ALERTA.exception("Timeout ao chamar a API: %s", e)
        return
    except requests.exceptions.ConnectionError as e:
        logger_ALERTA.exception("Erro de conexão com a API: %s", e)
        return
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', 'desconhecido')
        logger_ALERTA.exception("Resposta HTTP inválida: %s - status: %s", e, status)
        return
    except requests.exceptions.RequestException as e:
        logger_ALERTA.exception("Erro não esperado ao chamar a API: %s", e)
        return
    finally:
        try:
            s.close()
        except Exception:
            pass

def list_movest_edit(CODIGO, QTD):

    url_mov = os.getenv("ENDPOINT_LIST")
    token_mov = os.getenv("TOKEN_LIST")

    if not url_mov:
        logger_ALERTA.error("ENDPOINT não definido nas variáveis de ambiente.")
        raise ValueError("ENDPOINT não definido")

    if not token_mov:
        logger_ALERTA.error("TOKEN não definido nas variáveis de ambiente.")
        raise ValueError("TOKEN não definido")

    payload = {
        "token": token_mov,
        "estoque": "Estoque Principal",
        "data_inicio": "2026-01-01",
        "data_fim": "2030-01-15", 
        "status": "Em Aberto",
        "codigo_material": CODIGO,
    }

    headers = {}

    s = _create_session_with_retries()

    try:
        prepped = Request('POST', url_mov, json=payload, headers=headers).prepare()
        response = s.send(prepped, timeout=10)

        # Lança exceção para status codes 4xx/5xx
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as e:
            logger_ALERTA.exception("Erro ao decodificar JSON da resposta: %s", e)
            return pd.DataFrame()

        df = pd.DataFrame(data)
        logger_SIMPLES.info(df)
        logger_SIMPLES.info(response.status_code)
        # Editamos o movimento de estoque com a data de recebimento
        id = df.loc[0, "ID"]

        edit_movest(id, CODIGO, QTD)

        return 

    except requests.exceptions.Timeout as e:
        logger_ALERTA.exception("Timeout ao chamar a API: %s", e)
        return
    except requests.exceptions.ConnectionError as e:
        logger_ALERTA.exception("Erro de conexão com a API: %s", e)
        return
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', 'desconhecido')
        logger_ALERTA.exception("Resposta HTTP inválida: %s - status: %s", e, status)
        return
    except requests.exceptions.RequestException as e:
        logger_ALERTA.exception("Erro não esperado ao chamar a API: %s", e)
        return
    finally:
        try:
            s.close()
        except Exception:
            pass


if __name__ == "__main__":
    list_movest_edit(17052, 1)

