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

def listar_mov():
    url = os.getenv("ENDPOINT_LISTAR_MOV")
    TOKEN = os.getenv("TOKEN_LISTAR_MOV")

    if not url:
        logger_ALERTA.error("ENDPOINT não definido nas variáveis de ambiente.")
        raise ValueError("ENDPOINT não definido")
    
    if not TOKEN:
        logger_ALERTA.error("TOKEN não definido nas variáveis de ambiente.")
        raise ValueError("TOKEN não definido")
    
    payload = {
        "token": TOKEN,
        "estoque": "Estoque Principal",
        "data_inicio": "2021-01-01",
        "status": "Recebido"
    }

    headers = {}

    session = _create_session_with_retries()

    try:
        response = session.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()  # Levanta um erro para códigos de status 4xx/5xx
        data = response.json()
        df_mov = pd.DataFrame(data)
        return df_mov
    
    except requests.RequestException as e:
        logger_ALERTA.error(f"Erro na requisição: {e}")
        raise
    except ValueError as e:
        logger_ALERTA.error(f"Erro ao processar a resposta JSON: {e}")
        raise
