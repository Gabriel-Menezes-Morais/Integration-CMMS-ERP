import requests
from requests import Request, Session   
import pandas as pd
import os
import logging
from dotenv import load_dotenv

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

def extract():

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

if __name__ == "__main__":
    df = extract()
    print(df)
