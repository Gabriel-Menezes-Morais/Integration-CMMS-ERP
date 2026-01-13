import pandas as pd
import integra_API_Usuarios
import logging
import yaml
import os
from dotenv import load_dotenv

load_dotenv()

def gerar_senha(nome_completo):
    # Gera uma senha simples a partir do nome completo para cadastro de usuários
    partes = nome_completo.strip().split()
    partes = [parte.lower() for parte in partes]

    if len(partes) < 2:
        return f"{partes[0]}@26!"  # Se tiver só um nome, retorna ele com um sufixo fixo

    primeiro_nome = partes[0]
    sobrenome = partes[-1]
    senha = f"{primeiro_nome[0]}{sobrenome}@26!"  # Por exemplo, Gabriel Silva -> gabrielsilva123

    return senha

def gerar_username(nome_completo):
    # Gera um username simples a partir do nome completo para cadastro de usuários

    partes = nome_completo.strip().split()
    partes = [parte.lower() for parte in partes]

    # Se tiver só um nome, retorna ele todo em minúsculo
    if len(partes) < 2:
        return nome_completo.lower()
    
    primeiro_nome = partes[0]
    sobrenome = partes[-1]
    username = f"{primeiro_nome[0]}{sobrenome}" # Por exemplo, Gabriel Silva -> gsilva

    return username

def transformar_usuarios():

    """
    Transforma os dados extraídos da API de usuários em um DataFrame estruturado. 
    Salva os dados transformados em um arquivo YAML para uso na autenticação do Streamlit.
    """

    logger_Alerta = logging.getLogger("app")
    logger_Comum = logging.getLogger("app.lowlevel")

    try:
        # Extrai os dados usando a função do módulo teste_api_autent
        df_usuarios = integra_API_Usuarios.extract()
        
        if df_usuarios.empty:
            logger_Alerta.warning("Nenhum dado de usuário foi extraído da API.")
            return pd.DataFrame()  # Retorna um DataFrame vazio se não houver dados
        
        # Exemplo de transformação: Selecionar colunas relevantes e renomeá-las
        colunas_relevantes = {
            'ID': 'ID_Usuario',
            'Nome': 'Nome',
            'e-mail': 'Email',
            'Acesso': 'Ativo',
            'Executante': 'Executante'
        }
        
        # Realiza as transformações necessárias
        df_transformado = df_usuarios[list(colunas_relevantes.keys())].rename(columns=colunas_relevantes)
        df_transformado = df_transformado.drop_duplicates(subset=['ID_Usuario'])
        df_transformado = df_transformado[df_transformado['Executante'] == 'Sim']

        # Converter a coluna 'Ativo' para booleano
        df_transformado['Ativo'] = df_transformado['Ativo'].astype(bool)

        logger_Comum.info(f"Transformação concluída com sucesso. Total de usuários transformados: {len(df_transformado)}")
        
        usernames_dict = {}

        # Monta o dicionário de usuários para o YAML
        for id, row in df_transformado.iterrows():
            
            senha = gerar_senha(row['Nome'])
            user_key = gerar_username(row['Nome'])

            usernames_dict[user_key] = {
                    'id': row['ID_Usuario'],
                    'email': row['Email'],
                    'name': row['Nome'],
                    'password': senha, # O JSON não tem senha, definimos um padrão
                    'ativo': row['Ativo'],
                    'executante': row['Executante']
                    }

        cookie = os.getenv("COOKIE_KEY")
        # Monta a estrutura final completa
        yaml_data = {
            'credentials': {
                'usernames': usernames_dict
            },
            'cookie': {
                'expiry_days': 30,
                'key': cookie,
                'name': 'cookieteste'
            }
        }

        # Salva o YAML em um arquivo
        with open('config.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(yaml_data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return df_transformado
    
    except Exception as e:
        logger_Alerta.exception(f"Erro durante a transformação dos dados de usuários: {e}")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro
    
if __name__ == "__main__":
    df_usuarios_transformados = transformar_usuarios()
    print(df_usuarios_transformados)
