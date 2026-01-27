import streamlit as st
import json
import os
import time
from services.integra_API_Cadastro import Cadastrar
from database.funcoesBD import CadastrarBD
import streamlit_authenticator as st_auth
import yaml
from yaml.loader import SafeLoader

# INTERFACE DO USUÁRIO
st.set_page_config(page_title="CaldMAN/Cadastrar_Item", layout="wide")

# Carregamento do arquivo de configuração de usuários
@st.cache_data
def users_file():
    with open('config/config.yaml', 'r') as file:
        config = yaml.load(file, Loader=SafeLoader)
    return config

# Carrega a configuração de usuários
config = users_file()

# Configuração do autenticador
authenticator = st_auth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Tela de login
authenticator.login()
# Verifica se o usuário está autenticado
if st.session_state["authentication_status"]:

    authenticator.logout('Logout', 'sidebar')
    st.sidebar.write(f'Bem-vindo, *{st.session_state["name"]}*')
    
    # Configuração da barra lateral
    st.sidebar.title("Informações")
    st.sidebar.info("Sistema de Geração de Necessidades v1.0\nDesenvolvido por Gabriel D'Amata")

    st.sidebar.markdown("---")

    st.sidebar.info("Cadastro de Materiais:\nCrie novos itens de manutenção seguindo o padrão PDM com código automático.")

    st.sidebar.markdown("---")

    st.sidebar.write("Sobre esta página:")
    st.sidebar.write("Nesta página você pode cadastrar novos materiais no sistema SGMAN seguindo o padrão **PDM (Product Data Management)**.")
    
    st.sidebar.markdown("--")
    
    st.sidebar.write("**Como cadastrar um item:**")
    st.sidebar.write("1. **Família**: Selecione ou crie uma nova família (ex: PARAFUSO, ROLAMENTO)")
    st.sidebar.write("2. **Tipo**: Escolha o tipo ou crie um novo (ex: SEXTAVADO, ALLEN)")
    st.sidebar.write("3. **Variação**: Adicione variações se necessário (ex: ZINCADO, POLIDO)")
    st.sidebar.write("4. **Especificações**: Preencha os atributos técnicos")
    st.sidebar.write("5. **Unidade**: Selecione a unidade de medida")
    st.sidebar.write("6. **Cadastrar**: Revise e confirme o cadastro")

    st.sidebar.markdown("--")

    st.sidebar.write("💡 **Obs.:** O código é gerado automaticamente no formato **MNTXXXX** e a descrição segue o padrão PDM.")

    st.sidebar.markdown("---")
    
    from dotenv import load_dotenv
    load_dotenv()
    email_dev = os.getenv("EMAIL_DEV")
    
    st.sidebar.write("Para mais informações, entre em contato com o desenvolvedor:")
    st.sidebar.caption(f"e-mail:\n{email_dev}")

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
                            "variacoes": ["ZINCADO", "POLIDO"],
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
        with open(FILE_TAXONOMIA, "r", encoding="utf-8") as f:
            return json.load(f)

    def salvar_taxonomia(dados):
        # Salva a estrutura da árvore em arquivo JSON
        with open(FILE_TAXONOMIA, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    # Função para gerar Código Auto-Incremental (MNT0000, MNT0001...)
    def gerar_proximo_codigo():
        if not os.path.exists(FILE_ITENS):
            return "MNT0000"

        with open(FILE_ITENS, "r", encoding="utf-8") as f:
            itens = json.load(f)

        if not itens:
            return "MNT0000"

        # Normaliza prefixo (ex: mnt00) e considera apenas a parte numérica
        codigos_validos = []
        for item in itens:
            codigo_bruto = str(item.get("codigo", "")).upper()
            numericos = "".join(ch for ch in codigo_bruto if ch.isdigit())
            if not numericos:
                continue
            try:
                codigos_validos.append(int(numericos))
            except ValueError:
                continue

        if not codigos_validos:
            return "MNT0000"

        novo_numero = max(codigos_validos) + 1
        return f"MNT{novo_numero:04d}"

    

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
        familia_selecionada = st.selectbox("1. Nome Básico (Família) *", familias)

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
        tipo_sel = st.selectbox("2. Modificador (Tipo) *", modificadores)
        
        # Lógica de Criação de Tipo 
        if tipo_sel == "➕ Novo Tipo...":
            st.info("Configurando novo Tipo...")
            novo_tipo = st.text_input("Nome (Ex: SEXTAVADO):").upper()
            # Adjetivos
            input_vars = st.text_input("Variações/Adjetivos possíveis (Ex: AZUL, ZINCADO):").upper()
            # Specs Técnicas
            input_specs = st.text_input("Atributos Técnicos (Ex: Diâmetro, Comprimento):").upper()
            
            if st.button("Salvar Tipo"):
                if novo_tipo and input_specs:
                    # Transforma "SEXTAVADO, ALLEN" em ["SEXTAVADO", "ALLEN"]
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

    # Modal para adicionar variação
    @st.dialog("Nova Variação")
    def modal_adicionar_variacao():
        nova_var = st.text_input("Digite a nova Variação (Ex: VERMELHO):").upper()
        col_modal1, col_modal2 = st.columns(2)
        with col_modal1:
            if st.button("Salvar", use_container_width=True):
                if nova_var:
                    dados_tipo["variacoes"].append(nova_var)
                    taxonomia[familia_selecionada]["modificadores"][tipo_sel] = dados_tipo
                    salvar_taxonomia(taxonomia)
                    st.rerun()
                else:
                    st.error("Informe o nome da variação.")
        with col_modal2:
            if st.button("Cancelar", use_container_width=True):
                st.rerun()

    with col3:
        # Se não houver variações cadastradas, nem mostra o campo ou mostra "PADRÃO"
        if not dados_tipo.get("variacoes"): 
            var_sel = None
            st.caption("Sem variações visuais para este item.")
            if st.button("➕ Criar Variação"):
                modal_adicionar_variacao()
        else:
            var_sel = st.selectbox("3. Variação / Acabamento", lista_variacoes)
            if var_sel == "➕ Adicionar Variação...":
                modal_adicionar_variacao()

    unidade_options = ["pc", "g", "kg", "l", "m", "cm", "m2", "ct", "mm"] # Unidades em sigla de acordo com o SGMAN
    with col4:
        # Unidade do item  
        unidade_selecionada = st.selectbox("4. Unidade de Medida *", unidade_options)

    # Adição de nova especificação técnica para o tipo selecionado
    st.markdown("---")
    st.caption("Ajuste as especificações técnicas do tipo selecionado antes de preencher os valores.")
    with st.expander("➕ Adicionar especificação técnica"):
        nova_spec = st.text_input(
            "Nova especificação técnica (Ex: ROSCA, ESPESSURA)",
            key=f"nova_spec_{familia_selecionada}_{tipo_sel}"
        ).upper()

        if st.button("Salvar especificação", key=f"btn_salvar_spec_{familia_selecionada}_{tipo_sel}"):
            if nova_spec:
                if nova_spec not in dados_tipo["specs"]:
                    dados_tipo["specs"].append(nova_spec)
                    taxonomia[familia_selecionada]["modificadores"][tipo_sel] = dados_tipo
                    salvar_taxonomia(taxonomia)
                    st.success(f"Especificação '{nova_spec}' adicionada ao tipo {tipo_sel}.")
                    st.rerun()
                else:
                    st.warning("Esta especificação já existe para este tipo.")
            else:
                st.error("Informe o nome da especificação.")

    # ATRIBUTOS TÉCNICOS
    st.divider()
    st.subheader("Especificações Técnicas *")

    # Pega a lista de atributos necessários para essa combinação
    specs_necessarias = dados_tipo["specs"]
    valores_atributos = {}

    if not specs_necessarias:
        st.info("Este tipo ainda não possui especificações. Adicione uma acima para continuar.")
    else:
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
            try:
                Cadastrar(novo_item)
            except Exception as e:
                st.error(f"Erro ao cadastrar no SGMAN: {e}")
                st.stop()
            
            
            
            try:
                CadastrarBD(novo_item)
            except Exception as e:
                st.error(f"Erro ao cadastrar no ERP: {e}")
                st.stop()

            # Salvamento local
            try:
                with open(FILE_ITENS, "r", encoding="utf-8") as f:
                    db_itens = json.load(f)
            except:
                db_itens = []
                
            db_itens.append(novo_item)
            with open(FILE_ITENS, "w", encoding="utf-8") as f:
                json.dump(db_itens, f, indent=4, ensure_ascii=False)
                
            st.success(f"Item {codigo_gerado} cadastrado com sucesso: {descricao_padrao}")
            time.sleep(3)

            # Aguarda um pouco e recarrega para atualizar o código mnt
            st.rerun()