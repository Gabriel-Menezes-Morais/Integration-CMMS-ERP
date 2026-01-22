import streamlit as st
import json
import os
import time
from services.integra_API_Cadastro import Cadastrar
from database.funcoesBD import CadastrarBD

#CONFIGURAÇÃO DE DADOS (SIMULANDO BANCO DE DADOS)
FILE_TAXONOMIA = "taxonomia_materiais.json"
FILE_ITENS = "itens_cadastrados.json"

# Função para carregar a estrutura da árvore (Famílias e Regras)
def carregar_taxonomia():
    if not os.path.exists(FILE_TAXONOMIA):
        # Exemplo inicial baseado na sua lógica
        dados_iniciais = {
            "PARAFUSO": {
                "modificadores": {
                    "SEXTAVADO": ["Material", "Diâmetro", "Comprimento", "Tipo de Rosca"],
                    "ALLEN": ["Material", "Diâmetro", "Comprimento", "Cabeça"]
                }
            },
            "ROLAMENTO": {
                "modificadores": {
                    "ESFERA": ["Série", "Blindagem", "Folga"],
                    "ROLOS": ["Série", "Tipo"]
                }
            }
        }
        salvar_taxonomia(dados_iniciais)
        return dados_iniciais
    with open(FILE_TAXONOMIA, "r") as f:
        return json.load(f)

def salvar_taxonomia(dados):
    with open(FILE_TAXONOMIA, "w") as f:
        json.dump(dados, f, indent=4)

# Função para gerar Código Auto-Incremental (mnt00, mnt01...)
def gerar_proximo_codigo():
    if not os.path.exists(FILE_ITENS):
        return "mnt00"
    
    with open(FILE_ITENS, "r") as f:
        itens = json.load(f)
    
    if not itens:
        return "mnt00"
    
    # Pega o último código (ex: mnt15), tira o 'mnt', vira int e soma 1
    ultimos_codigos = [int(item['codigo'].replace('mnt', '')) for item in itens]
    novo_numero = max(ultimos_codigos) + 1
    return f"mnt{novo_numero:02d}"

# INTERFACE DO USUÁRIO
st.set_page_config(page_title="Cadastro PDM", layout="wide")

#Configurações manuais de CSS da página
@st.cache_data
def inject_css():
    with open("custom/style.css") as file:
        st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)
    return

# Injeção do CSS personalizado
inject_css()

# Título da página
colspace1, coltitle, colspace2 = st.columns([0.1, 0.7, 0.1])
with coltitle:
    st.write("""
        # Cadastro de Materiais
    """)
with colspace1:
    st.write("")
    pass
with colspace2:
    st.write("")
# Carrega dados
taxonomia = carregar_taxonomia()
familias = list(taxonomia.keys()) + ["➕ Nova Família..."]

# NOME BÁSICO (FAMÍLIA)
col1, col2, col3 = st.columns(3)
with col1:
    familia_selecionada = st.selectbox("1. Nome Básico (Família)", familias)

# Lógica para adicionar nova família
if familia_selecionada == "➕ Nova Família...":
    nova_familia = st.text_input("Digite o nome da nova Família (Ex: DISCO):").upper()
    if st.button("Criar Família"):
        if nova_familia and nova_familia not in taxonomia:
            taxonomia[nova_familia] = {"modificadores": {}}
            salvar_taxonomia(taxonomia)
            st.rerun()
    st.stop() # Para aqui até criar

# MODIFICADOR (TIPO)
modificadores = list(taxonomia[familia_selecionada]["modificadores"].keys()) + ["➕ Novo Tipo..."]

with col2:
    modificador_selecionado = st.selectbox("2. Modificador (Tipo)", modificadores)

unidade_options = ["Pç", "g", "kg", "l", "m", "cm", "m2", "ct"]
with col3:
    # Unidade do item  
    unidade_selecionada = st.selectbox("Unidade de Medida", unidade_options)

# Lógica para adicionar novo modificador/tipo
if modificador_selecionado == "➕ Novo Tipo...":
    st.info(f"Cadastrando novo tipo para {familia_selecionada}")
    novo_modificador = st.text_input("Nome do Tipo (Ex: DE CORTE):").upper()
    # O usuário define quais atributos esse tipo precisa ter
    novos_atributos = st.text_input("Quais atributos técnicos? (Separe por vírgula. Ex: Diâmetro, Furo, Espessura)")
    
    if st.button("Criar Tipo"):
        if novo_modificador:
            lista_attrs = [a.strip() for a in novos_atributos.split(",")]
            taxonomia[familia_selecionada]["modificadores"][novo_modificador] = lista_attrs
            salvar_taxonomia(taxonomia)
            st.rerun()
    st.stop()

# ATRIBUTOS TÉCNICOS
st.divider()
st.subheader("Especificações Técnicas")

# Pega a lista de atributos necessários para essa combinação
atributos_necessarios = taxonomia[familia_selecionada]["modificadores"][modificador_selecionado]
valores_atributos = {}

# Cria colunas dinamicamente para não ficar uma lista vertical gigante
cols = st.columns(len(atributos_necessarios)) 

for i, attr in enumerate(atributos_necessarios):
    with cols[i]:
        # Aqui você poderia criar selects específicos se quisesse ser mais rígido
        valores_atributos[attr] = st.text_input(f"{attr}").upper()

# GERAÇÃO AUTOMÁTICA DA DESCRIÇÃO (PDM)
# Lógica: NOME BÁSICO + MODIFICADOR + ATRIBUTOS
str_atributos = " ".join(valores_atributos.values())
descricao_padrao = f"{familia_selecionada} {modificador_selecionado} {str_atributos}".strip()

st.markdown("---")
st.caption("Pré-visualização do Padrão:")
st.code(descricao_padrao, language="text")

codigo_gerado = gerar_proximo_codigo()

# BOTÃO DE ENVIO (API/SALVAR)
if st.button("✅ Cadastrar Item no SGMAN"):
    # Verifica se todos os campos foram preenchidos
    if "" in valores_atributos.values():
        st.error("Preencha todas as especificações técnicas!")
    else:
        novo_item = {
            "codigo": codigo_gerado,
            "descricao": descricao_padrao,
            "familia": familia_selecionada,
            "tipo": modificador_selecionado,
            "detalhes": valores_atributos,
            "unidade": unidade_selecionada
        }

        # Chama a função de cadastro na API
        Cadastrar(novo_item)
        
        # Cadastro no ERP
        CadastrarBD(novo_item)

        # Simulando salvamento local
        try:
            with open(FILE_ITENS, "r") as f:
                db_itens = json.load(f)
        except:
            db_itens = []
            
        db_itens.append(novo_item)
        with open(FILE_ITENS, "w") as f:
            json.dump(db_itens, f, indent=4)
            
        st.success(f"Item {codigo_gerado} cadastrado com sucesso: {descricao_padrao}")
        st.balloons()
        time.sleep(3)
        # Aguarda um pouco e recarrega para atualizar o código mnt
        st.rerun()