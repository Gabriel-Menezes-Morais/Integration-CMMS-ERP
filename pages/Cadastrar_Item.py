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
                    "SEXTAVADO": { 
                        "variacoes": ["AZUL", "ZINCADO", "POLIDO"],
                        "specs": ["Material", "Diâmetro", "Comprimento", "Tipo de Rosca"] 
                        },
                    "ALLEN": { 
                        "variacoes": [], 
                        "specs": ["Material", "Diâmetro", "Comprimento", "Cabeça"] 
                              }
                }
            },
            "ROLAMENTO": {
                "modificadores": {
                    "ESFERA":{ 
                        "variacoes": [], 
                        "specs": ["Série", "Blindagem", "Folga"] 
                        },
                    "ROLOS": { 
                        "variacoes": [], 
                        "specs": ["Série", "Tipo"] 
                        }
                }
            }
        }
        
        salvar_taxonomia(dados_iniciais)
        return dados_iniciais
    with open(FILE_TAXONOMIA, "r") as f:
        return json.load(f)

def salvar_taxonomia(dados):
    # Salva a estrutura da árvore em arquivo JSON
    with open(FILE_TAXONOMIA, "w") as f:
        json.dump(dados, f, indent=4)

# Função para gerar Código Auto-Incremental (mnt00, mnt01...)
def gerar_proximo_codigo():
    if not os.path.exists(FILE_ITENS):
        return "mnt0000"
    
    # Carrega os itens já cadastrados
    with open(FILE_ITENS, "r") as f:
        itens = json.load(f)
    
    if not itens:
        return "mnt0000"
    
    # Pega o último código (ex: mnt15), tira o 'mnt', vira int e soma 1
    ultimos_codigos = [int(item['codigo'].replace('mnt', '')) for item in itens]
    novo_numero = max(ultimos_codigos) + 1
    return f"mnt{novo_numero:04d}"

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

# Listas principais
familias = list(taxonomia.keys()) + ["➕ Nova Família..."] # Opção para nova família

# NOME BÁSICO (FAMÍLIA)
col1, col2, col3, col4 = st.columns(4)
with col1:
    familia_selecionada = st.selectbox("1. Nome Básico (Família)", familias)

# Lógica para adicionar nova família
if familia_selecionada == "➕ Nova Família...":
    nova_familia = st.text_input("Digite o nome da nova Família (Ex: DISCO):").upper()
    # Botão para criar
    if st.button("Criar Família"):
        if nova_familia and nova_familia not in taxonomia:
            taxonomia[nova_familia] = {"modificadores": {}} # Inicializa com dict vazio
            salvar_taxonomia(taxonomia)
            st.rerun()
    st.stop() # Para aqui até criar

# MODIFICADOR (TIPO)
modificadores = list(taxonomia[familia_selecionada]["modificadores"].keys()) + ["➕ Novo Tipo..."] # Modificadores disponíveis

with col2:
    tipo_sel = st.selectbox("2. Tipo", modificadores)
    
    # Lógica de Criação de Tipo (ATUALIZADA)
    if tipo_sel == "➕ Novo Tipo...":
        st.info("Configurando novo Tipo...")
        novo_tipo = st.text_input("Nome (Ex: SEXTAVADO):").upper()
        # Adjetivos
        input_vars = st.text_input("Variações/Adjetivos possíveis (Ex: AZUL, ZINCADO):")
        # Specs Técnicas
        input_specs = st.text_input("Atributos Técnicos (Ex: Diâmetro, Comprimento):")
        
        if st.button("Salvar Tipo"):
            if novo_tipo and input_specs:
                lista_vars = [v.strip() for v in input_vars.split(",")] if input_vars else [] # Lista de variações
                lista_specs = [s.strip() for s in input_specs.split(",")] # Lista de specs
                
                # Salva na estrutura nova (dict com 2 listas)
                taxonomia[familia_selecionada]["modificadores"][novo_tipo] = {
                    "variacoes": lista_vars,
                    "specs": lista_specs
                }
                salvar_taxonomia(taxonomia)
                st.rerun()
        st.stop()

# Variação (Adjetivo)

dados_tipo = taxonomia[familia_selecionada]["modificadores"][tipo_sel] # Dados do tipo selecionado
lista_variacoes = dados_tipo.get("variacoes", []) + ["➕ Adicionar Variação..."] # Opção para adicionar variação

with col3:
        # Se não houver variações cadastradas, nem mostra o campo ou mostra "PADRÃO"
    if not dados_tipo.get("variacoes"):
        var_sel = None
        st.caption("Sem variações visuais para este item.")
        if st.button("➕ Criar Variação"): # Botão para adicionar tardiamente
             # Pequeno hack para forçar entrada no modo de criação
             # Numa app real, seria um modal, aqui simplifiquei
             st.session_state['add_var_mode'] = True 
    else:
        var_sel = st.selectbox("3. Variação / Acabamento", lista_variacoes)

    # Lógica para adicionar variação em um item que já existe
    if var_sel == "➕ Adicionar Variação..." or st.session_state.get('add_var_mode'):
        nova_var = st.text_input("Nova Variação (Ex: VERMELHO):").upper()
        if st.button("Salvar Variação"):
            if nova_var:
                dados_tipo["variacoes"].append(nova_var)
                taxonomia[familia_selecionada]["modificadores"][tipo_sel] = dados_tipo # Atualiza
                salvar_taxonomia(taxonomia)
                st.session_state['add_var_mode'] = False
                st.rerun()
        st.stop() # o método st.stop() interrompe a execução aqui para evitar erros

unidade_options = ["Pç", "g", "kg", "l", "m", "cm", "m2", "ct"] # Unidades em sigla de acordo com o SGMAN
with col4:
    # Unidade do item  
    unidade_selecionada = st.selectbox("Unidade de Medida", unidade_options)

# ATRIBUTOS TÉCNICOS
st.divider()
st.subheader("Especificações Técnicas")

# Pega a lista de atributos necessários para essa combinação
specs_necessarias = dados_tipo["specs"]
valores_atributos = {}
cols = st.columns(len(specs_necessarias))
# Cria colunas dinamicamente para não ficar uma lista vertical gigante
cols = st.columns(len(specs_necessarias)) 

for i, attr in enumerate(specs_necessarias):
    with cols[i]:
        # Aqui você poderia criar selects específicos se quisesse ser mais rígido
        valores_atributos[attr] = st.text_input(f"{attr}").upper()

# GERAÇÃO AUTOMÁTICA DA DESCRIÇÃO (PDM)
# Lógica: NOME BÁSICO + MODIFICADOR + VARIAÇÕES + ATRIBUTOS
partes_nome = [familia_selecionada, tipo_sel]

if var_sel and var_sel != "➕ Adicionar Variação...":
    partes_nome.append(var_sel)  # Insere a variação entre família e tipo
partes_nome.extend(valores_atributos.values())
descricao_padrao = " ".join([p for p in partes_nome if p]).strip()
st.markdown("---")
st.caption("Pré-visualização do Padrão:")
st.code(descricao_padrao, language="text")

codigo_gerado = gerar_proximo_codigo()

# BOTÃO DE ENVIO
if st.button("✅ Cadastrar Item no SGMAN"):
    # Verifica se todos os campos foram preenchidos
    if "" in valores_atributos.values():
        st.error("Preencha todas as especificações técnicas!")
    else:
        novo_item = {
            "codigo": codigo_gerado,
            "descricao": descricao_padrao,
            "familia": familia_selecionada,
            "tipo": tipo_sel,
            "detalhes": valores_atributos,
            "unidade": unidade_selecionada
        }

        # Chama a função de cadastro na API
        Cadastrar(novo_item)
        
        # Cadastro no ERP
        CadastrarBD(novo_item)

        # Salvamento local
        try:
            with open(FILE_ITENS, "r") as f:
                db_itens = json.load(f)
        except:
            db_itens = []
            
        db_itens.append(novo_item)
        with open(FILE_ITENS, "w") as f:
            json.dump(db_itens, f, indent=4)
            
        st.success(f"Item {codigo_gerado} cadastrado com sucesso: {descricao_padrao}")
        time.sleep(4)
        # Aguarda um pouco e recarrega para atualizar o código mnt
        st.rerun()