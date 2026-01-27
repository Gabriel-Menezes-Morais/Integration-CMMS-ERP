import os
import streamlit as st
from services.integra_API_Usuarios import list_movest_edit
from database.funcoesBD import deletar_item_carrinho, carrinho_full_filtrado
from services.integra_API_ListarPecas import extract
import json
import logging
from dotenv import load_dotenv
import streamlit_authenticator as st_auth
import pandas as pd
import time
import yaml
from yaml.loader import SafeLoader
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(page_title="CaldMAN/Histórico_de_Necessidades", layout="wide")

# resetar estado de sessão para atualização da checkbox
def resetar_sessao_checkbox(chave_prefixo, total_itens):
    for i in range(total_itens):
        chave = f"{chave_prefixo}_{i}"
        if chave in st.session_state:
            del st.session_state[chave]
    
    st.rerun()


# Configuração do logger
@st.cache_data
def load_logger_config():
    with open("config/log_config.json", "r") as f:
        return json.load(f)

configLOG = load_logger_config()
logging.config.dictConfig(configLOG)
logger_info = logging.getLogger("app.lowlevel")

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

# Bloco principal da aplicação, apenas acessível se o usuário estiver autenticado
if st.session_state["authentication_status"]:

    # Medição do tempo de execução do script
    start_time = time.time()

    # Opção de logout
    authenticator.logout('Logout', 'sidebar')
    st.sidebar.write(f'Bem-vindo, *{st.session_state["name"]}*')

    @st.cache_data
    def load_env():
        return load_dotenv()
    
    load_env()

    email_dev = os.getenv("EMAIL_DEV")

    # Configuração da barra lateral
    st.sidebar.title("Informações")
    st.sidebar.info("Sistema de Geração de Necessidades v1.0\nDesenvolvido por Gabriel D'Amata")

    st.sidebar.markdown("---")

    st.sidebar.info("Histórico de Necessidades:\nVeja todas as necessidades geradas com opções de filtro por data, código e descrição.")

    st.sidebar.markdown("---")

    st.sidebar.write("Sobre esta página:")
    st.sidebar.write("Nesta página você pode visualizar todas as necessidades que foram geradas. " \
    "Para necessidades **pendentes**, você pode desfazer o pedido. " \
    "Para necessidades **concluídas**, você pode marcar como recebido.")

    st.sidebar.markdown("--")

    st.sidebar.write("Para mais informações, entre em contato com o desenvolvedor:")
    st.sidebar.caption(f"e-mail:\n{email_dev}")


    #Configurações manuais de CSS da página
    @st.cache_data
    def inject_css():
        with open("custom/style.css") as file:
            st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)
        return
    
    # Injeção do CSS personalizado
    inject_css()


    # Cabeçalho da página
    colspace1, coltitle, colspace2 = st.columns([0.1, 0.7, 0.1])
    with coltitle:
        st.write("""
            # Histórico de Necessidades
        """)
    with colspace1:
        st.write("")
        pass
    with colspace2:
        st.write("")
    st.markdown("---")

    # Função de confirmação de recebimento de itens
    @st.dialog("⚠️ Confirmação Necessária")
    def abrir_confirmacao(chaves_recebidos, itens_recebidos):
        st.write(f"Há itens selecionados como recebido.")
        st.write(f"Você tem certeza do recebimento desse item?")
        st.write("Essa ação não pode ser desfeita.")
        
        col1, col2 = st.columns(2)
        
        with col1:
           
            try:
                if st.button("Sim", type="primary"):
                    for item in itens_recebidos:
                        list_movest_edit(item[0], item[1])
                    logger_info.info("O usuário confirmou o recebimento dos itens.")
                    resetar_sessao_checkbox("checkbox_recebido", len(itens_recebidos))
            except KeyError:
                logger_info.info("O usuário marcou um item já recebido")
                st.write(f"O item {item} já foi marcado como recebido.")
                
        with col2:
            if st.button("Cancelar"):
                # Limpa os estados de sessão associados às chaves recebidas
                for chave in chaves_recebidos:
                    if chave in st.session_state:
                        del st.session_state[chave]
                st.rerun()

    # Carregamento dos dados
    def load_data():
        try:
            if 'df_extract' not in st.session_state:
                logger_info.info("Extraindo dados de produtos do API...")
                st.session_state['df_extract'] = extract()
            if 'df_pedidos' not in st.session_state:
                logger_info.info("Carregando dados do carrinho de necessidades...")
                st.session_state['df_pedidos'] = carrinho_full_filtrado()

            # Adiciona coluna de data se não existir
            if not st.session_state['df_pedidos'].empty and 'Data' not in st.session_state['df_pedidos'].columns:
                st.session_state['df_pedidos']['Data'] = datetime.now()
            
            return st.session_state['df_extract'], st.session_state['df_pedidos']
        except Exception as e:
            logger_info.error(f"Erro ao carregar dados: {e}")
            return None, None

    df_extract, df_pedidos = load_data()

    
    if df_pedidos is None or df_extract is None:
        st.error("Erro ao carregar os dados do banco de dados.")
    elif df_pedidos.empty:
        st.info("Nenhuma necessidade gerada ainda.")
    else:
        # Criar mapas de descrições e unidades
        desc_map = df_extract.set_index('Cód. Interno')['Descrição'].to_dict()
        un_map = df_extract.set_index('Cód. Interno')['Un.'].to_dict()

        # FILTROS
        st.subheader("Filtros de Busca")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            status_filtro = st.selectbox(
                "Status",
                ["Todos", "Pendentes", "Concluídos"],
                key="status_filter"
            )

        with col2:
            # Filtro por data - início
            data_inicio = st.date_input(
                "Data de Início",
                value=datetime.now() - timedelta(days=30),
                key="data_inicio"
            )

        with col3:
            # Filtro por data - fim
            data_fim = st.date_input(
                "Data de Fim",
                value=datetime.now(),
                key="data_fim"
            )

        with col4:
            termo_busca = st.text_input(
                "🔍 Pesquisar (Código ou Descrição)",
                placeholder="Digite código ou descrição...",
                key="termo_busca"
            )

        # Botão para aplicar filtros
        col_button = st.columns([0.5, 0.5, 0.5, 0.5, 0.5])[0]
        with col_button:
            botao_filtrar = st.button("🔍 Aplicar Filtros", type="primary", use_container_width=True)

        st.markdown("---")

        # Aplicar filtros apenas quando o botão é clicado
        if botao_filtrar:
            st.session_state.filtros_aplicados = True
            st.session_state.filtro_status = status_filtro
            st.session_state.filtro_data_inicio = data_inicio
            st.session_state.filtro_data_fim = data_fim
            st.session_state.filtro_termo_busca = termo_busca
            logger_info.info(f"Filtros aplicados: Status={status_filtro}, Data={data_inicio} a {data_fim}, Busca='{termo_busca}'")

        # Recuperar filtros salvos da sessão
        if 'filtros_aplicados' not in st.session_state:
            st.session_state.filtros_aplicados = False

        # Aplicar filtros
        df_filtrado = df_pedidos.copy()

        if st.session_state.filtros_aplicados:
            # Filtro de status
            if st.session_state.filtro_status == "Pendentes":
                df_filtrado = df_filtrado[df_filtrado['IDPedCom'].isna()]
            elif st.session_state.filtro_status == "Concluídos":
                df_filtrado = df_filtrado[df_filtrado['IDPedCom'].notna()]

            # Filtro de data
            if not df_filtrado.empty:
                df_filtrado['Data'] = pd.to_datetime(df_filtrado['Data'], errors='coerce')
                df_filtrado = df_filtrado[
                    (df_filtrado['Data'].dt.date >= st.session_state.filtro_data_inicio) &
                    (df_filtrado['Data'].dt.date <= st.session_state.filtro_data_fim)
                ]

            # Filtro de busca (código e descrição)
            if st.session_state.filtro_termo_busca:
                termo_lower = st.session_state.filtro_termo_busca.lower()
                df_filtrado = df_filtrado[
                    (df_filtrado['CodProCOPY'].astype(str).str.lower().str.contains(termo_lower, na=False)) |
                    (df_filtrado['CodProCOPY']
                        .apply(lambda x: desc_map.get(x, ""))
                        .astype(str)
                        .str.lower()
                        .str.contains(termo_lower, na=False))
                ]
                logger_info.info(f"Usuário pesquisou por '{st.session_state.filtro_termo_busca}' no histórico de necessidades.")

        # Paginação
        ITENS_POR_PAGINA = 6

        if 'pagina_atual_hist' not in st.session_state:
            st.session_state.pagina_atual_hist = 0

        def resetar_pagina_hist():
            st.session_state.pagina_atual_hist = 0

        # Reseta página ao filtrar
        if termo_busca:
            resetar_pagina_hist()

        # Exibir tabela
        if df_filtrado.empty:
            st.warning("Nenhuma necessidade encontrada com os filtros aplicados.")
        else:
            total_itens = len(df_filtrado)
            st.caption(f"Mostrando resultados de {total_itens} necessidades.")

            # Cálculos dos índices (Onde começa e onde termina a fatia)
            inicio = st.session_state.pagina_atual_hist * ITENS_POR_PAGINA
            fim = inicio + ITENS_POR_PAGINA

            # Cria a sub-lista (Apenas os ITENS_POR_PAGINA itens da vez)
            lote_atual = df_filtrado[inicio:fim]

            st.caption(f"Mostrando {len(lote_atual)} de {total_itens} itens encontrados.")

            # Tabela com loop for
            with st.form("historico_necessidades"):
                for idx, (index, row) in enumerate(lote_atual.iterrows()):
                    
                    col1, col2, col3, col4, col5 = st.columns([0.3, 0.175, 0.175, 0.175, 0.175])

                    # Verificação do status do pedido
                    pendencia = 'pendente'
                    idped = row.get('IDPedCom', None)
                    data_recebimento = row.get('Data_Recebimento', None)

                    if idped is not None and pd.notna(idped):
                        pendencia = 'concluído'

                    item_codigo = row['CodProCOPY']
                    item_nome = desc_map.get(item_codigo, "N/A")

                    with col1:
                        if pendencia == "pendente":
                            # Item pendente, pode desfazer a necessidade
                            st.caption(":blue[Desfazer necessidade?]")
                            st.checkbox(
                                f"Descrição: {item_nome}", 
                                key=f"check_{item_codigo}_{idx}"
                            )
                        elif data_recebimento is None or pd.isna(data_recebimento):
                            # Item concluído mas não recebido, pode marcar como recebido
                            st.caption(":yellow[Item recebido?]")
                            st.checkbox(
                                f"Descrição: {item_nome}", 
                                key=f"recebido_{item_codigo}_{idx}"
                            )
                        else:
                            # Item já recebido - mostra mensagem
                            st.caption(":green[✅ Item já recebido]")
                            st.write(f"Descrição: {item_nome}")
                    
                    with col2:
                        st.write("")
                        st.write(f"Un.: {un_map.get(item_codigo, 'N/A')}")
                    
                    with col3:
                        st.write("")
                        st.write(f"Cód.: {item_codigo}")
                    
                    with col4:
                        st.write("")
                        st.write(f"Qtd: {row['Qtd']:.1f}")
                    
                    with col5:
                        st.write("")
                        if data_recebimento and pd.notna(data_recebimento):
                            st.write("✅ Recebido")
                        else:
                            st.write(f"{pendencia}")
                    
                    st.write('---')

                enviado = st.form_submit_button("Aplicar alterações")
            
            # Processamento dos itens
            if enviado:
                logger_info.info("Botão 'Aplicar alterações' foi pressionado.")

                itens_para_mover = []
                itens_recebidos = []
                chaves_recebidos = []

                for idx, (index, row) in enumerate(lote_atual.iterrows()):
                    item_codigo = row['CodProCOPY']

                    chave_checkbox = f"check_{item_codigo}_{idx}"
                    chave_checkbox_rec = f"recebido_{item_codigo}_{idx}"

                    if st.session_state.get(chave_checkbox, False):
                        itens_para_mover.append(item_codigo)
                        del st.session_state[chave_checkbox]
                    
                    if st.session_state.get(chave_checkbox_rec, False):
                        chaves_recebidos.append(st.session_state[chave_checkbox_rec])
                        itens_recebidos.append([item_codigo, row['Qtd']])

                logger_info.info(f"Itens para mover: {itens_para_mover}")
                logger_info.info(f"Itens recebidos: {itens_recebidos}")

                # Caso houver itens para receber
                if itens_recebidos:
                    abrir_confirmacao(chaves_recebidos, itens_recebidos)

                # Caso houver itens para desfazer necessidade
                if itens_para_mover:
                    logger_info.info(f"IDs para remover: {itens_para_mover}")
                    deletar_item_carrinho(itens_para_mover)
                    logger_info.info(f"Itens {', '.join(itens_para_mover)} removidos da tabela de necessidades no banco de dados.")

                    st.session_state['df_pedidos'] = [
                        item for item in st.session_state['df_pedidos'] if item['CodProCOPY'] not in itens_para_mover
                        ]
                    st.rerun()
                
                if not itens_para_mover and not itens_recebidos:
                    st.warning("Selecione pelo menos um item antes de enviar.")

            # Paginação
            col_ant, col_meio, col_prox = st.columns([1, 9.3, 1])

            num_pag_total = 1
            
            # Cálculo do número total de páginas
            if total_itens % ITENS_POR_PAGINA != 0:
                num_pag_total = int((total_itens / ITENS_POR_PAGINA + 1))
            else:
                num_pag_total = int((total_itens / ITENS_POR_PAGINA))

            if st.session_state.pagina_atual_hist + 1 != 1:
                with col_meio:
                    st.markdown(f"**Página {st.session_state.pagina_atual_hist + 1}-{num_pag_total}**")
            else:
                with col_ant:
                    st.markdown(f"**Página {st.session_state.pagina_atual_hist + 1}-{num_pag_total}**")

            # Botão anterior
            if st.session_state.pagina_atual_hist + 1 != 1:
                with col_ant:
                    if st.button("Anterior", icon=":material/line_start_arrow_notch:", width="stretch", key="button_ant_hist"):
                        if st.session_state.pagina_atual_hist > 0:
                            st.session_state.pagina_atual_hist -= 1
                            st.rerun()

            # Botão próximo
            if st.session_state.pagina_atual_hist + 1 != num_pag_total:
                with col_prox:
                    if fim < total_itens:
                        if st.button("Próximo", icon=":material/line_end_arrow_notch:", width="stretch", key="button_pos_hist"):
                            st.session_state.pagina_atual_hist += 1
                            st.rerun()

    # Medição do tempo de execução do script
    end_time = time.time()

    # Log do tempo de execução
    logger_info.info(f"tempo de execução do script: {end_time - start_time:.2f} segundos")

# Fim do bloco de autenticação
elif st.session_state["authentication_status"] is False:
    st.error('Usuário/senha incorreto')

elif st.session_state["authentication_status"] is None:
    st.warning('Por favor, insira seu usuário e senha')

