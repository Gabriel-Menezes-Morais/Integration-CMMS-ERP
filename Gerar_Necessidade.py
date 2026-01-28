import os
import streamlit as st
from database.funcoesBD import compra_item
from services.integra_API_ListarPecas import extract
from ETL.listas import listagem_nec
import json
import logging
from dotenv import load_dotenv
import streamlit_authenticator as st_auth
from logging.config import dictConfig
import time
import yaml
from yaml.loader import SafeLoader

st.set_page_config(page_title="CaldMAN/Gerar_Necessidade",layout="wide")

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

    @st.cache_data # Cache para evitar recarregamento desnecessário
    def load_env():
        # Carrega as variáveis de ambiente do arquivo .env
        return load_dotenv()
    
    load_env()

    email_dev = os.getenv("EMAIL_DEV")

    # Configuração da barra lateral
    # Barra lateral com informações sobre o sistema
    st.sidebar.title("Informações")
    st.sidebar.info("Sistema de Geração de Necessidades v1.0\nDesenvolvido por Gabriel D'Amata")

    st.sidebar.markdown("---")

    st.sidebar.info("Descrição do sistema:")
    st.sidebar.info("Sistema desenvolvido para automatizar a geração de necessidades de compra com base em regras pré-definidas, " \
    "integrando-se com o ERP existente na empresa. Facilita o processo de aquisição, garantindo que os itens necessários sejam identificados" \
    " e solicitados de forma eficiente.") 

    st.sidebar.markdown("---") 

    st.sidebar.info("AJUDA")

    st.sidebar.markdown("--")

    st.sidebar.write("Sobre Criar Necessidade")
    st.sidebar.write('Na tabela "SELECIONE OS ITENS" estarão os itens que estão abaixo do estoque mínimo necessário, isto é,' \
    'são necessários para o estoque de manutenção. Para gerar a necessidade do item, marque a caixa ao lado da descrição do item, após isso,' \
    'com a caixa marcada, selecione a quantidade da compra, considerando a unidade do item. Por fim, marque "Atualizar e enviar selecionados".')

    st.sidebar.markdown("--")

    st.sidebar.write('Observação: não selecione itens de diferentes páginas e envie. Faça página por página (se houver mais de uma).')
    st.sidebar.markdown("---")
    st.sidebar.write("Para mais informações, entre em contato com o desenvolvedor:")
    st.sidebar.caption("e-mail:\n{}".format(email_dev))

    imagem = os.getenv("IMAGE")
    
    # Configuração do logger
    @st.cache_data # Cache para evitar recarregamento desnecessário
    def load_logger_config():
        with open("config/log_config.json", "r") as f:
            configLOG = json.load(f)
        return configLOG
    configLOG = load_logger_config()

    logging.config.dictConfig(configLOG)

    logger_info = logging.getLogger("app.lowlevel")

    #Configurações manuais de CSS da página
    @st.cache_data
    def inject_css():
        with open("custom/style.css") as file:
            st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)
        return
    
    # Injeção do CSS personalizado
    inject_css()

    # Cabeçalho da página
    collogo, coltitle, colspace = st.columns([0.1, 0.7, 0.1])
    with coltitle:
        st.write("""
            # Geração de Necessidade
        """)
    with collogo:
        # st.image(imagem, width=250) # tempo de execução aumentado muito com a imagem
        pass
    with colspace:
        st.write("")

    col_header, col_button = st.columns([0.89, 0.11])

    with col_header:
        st.write('---')

    st.subheader("SELECIONE OS ITENS")

    # Inicialização dos session states necessários
    if 'extract' not in st.session_state:
        st.session_state.extract = extract()

    df_extract = st.session_state.extract
    if 'desc_map' not in st.session_state:
        st.session_state.desc_map = df_extract.set_index('Cód. Interno')['Descrição'].to_dict()
    
    if 'un_map' not in st.session_state:
        st.session_state.un_map = df_extract.set_index('Cód. Interno')['Un.'].to_dict()
    
    if 'estoque_min_map' not in st.session_state:
        st.session_state.estoque_min_map = df_extract.set_index('Cód. Interno')['Estoque Mín.'].to_dict()
    
    if 'estoque_map' not in st.session_state:
        st.session_state.estoque_map = df_extract.set_index('Cód. Interno')['Estoque'].to_dict()

    # Lista de necessidades (itens abaixo do estoque mínimo)
    if 'dataload' not in st.session_state:
        st.session_state.dataload = 0
    if 'necessidades' not in st.session_state or st.session_state.dataload == 0:
        st.session_state.necessidades = listagem_nec()
        st.session_state.dataload += 1

    ITENS_POR_PAGINA = 6

    if 'pagina_atual' not in st.session_state:
        st.session_state.pagina_atual = 0

    def resetar_pagina():
        st.session_state.pagina_atual = 0

    if not st.session_state.necessidades:
        st.success("Todos os itens foram adicionados!")
    else:
    
        if st.session_state.get("reset_input_busca", False):
            st.session_state["input_busca"] = ""
            st.session_state["reset_input_busca"] = False

        col_busca, _ = st.columns([0.5, 0.5])
        with col_busca:
            termo_busca = st.text_input(
                "🔍 Pesquisar Produto",
                placeholder="Digite o nome ou código...",
                key="input_busca"
            )
        # Se houver termo de busca, reseta a página para a primeira
        if termo_busca:
            resetar_pagina()
        
        lista_filtrada = []

        if not termo_busca:
            lista_filtrada = st.session_state.necessidades

        else:

            termo = termo_busca.lower()
            logger_info.info(f"Usuário pesquisou por '{termo_busca}' na lista de necessidades.")
            lista_filtrada = [
                item_id for item_id in st.session_state.necessidades
                if termo in str(item_id) or termo in st.session_state.desc_map.get(item_id, "").lower()
            ]

        if not lista_filtrada:

            if termo_busca:
                st.warning(f"Nenhum produto encontrado para '{termo_busca}'.")
            elif not termo_busca:
                st.warning("Nenhum produto encontrado na lista de necessidades.")
        else:
            total_itens = len(lista_filtrada)
            
            # Cálculos dos índices (Onde começa e onde termina a fatia)
            inicio = st.session_state.pagina_atual * ITENS_POR_PAGINA
            fim = inicio + ITENS_POR_PAGINA
            
            # Cria a sub-lista (Apenas os itens da vez, conforme ITENS_POR_PAGINA)
            lote_atual = lista_filtrada[inicio:fim]

            # Mostra em qual página estamos
            st.caption(f"Mostrando {len(lote_atual)} de {total_itens} itens encontrados.")

            # Tabela de amostragem dos itens para compra
            with st.form("Meu formulário de compras"):
                for item in lote_atual:

                    col1, col2, col3, col4, col5 = st.columns([0.4, 0.16, 0.16, 0.1, 0.26])

                    with col1:
                        
                        # Verificação para caso houver mais de um item com o mesmo Código Interno, por alguma falha externa
                        item_nome = st.session_state.desc_map.get(item, "")
                        if not item_nome:
                            continue
                        st.checkbox(item_nome, key=f"check_{item}")
                        #Criar uma opção para inserir observações relevantes para o comprador
                        if st.session_state[f"check_{item}"]:
                            st.text_area("Observações (opcional):", key=f"obs_{item}", height=50)
                    with col2:
                        st.write("Cód.: {}".format(item))
                    with col3:
                        st.write("Un.: {}".format(st.session_state.un_map.get(item, "")))
                    with col4:
                        # Informação de quanto é necessário para completar o estoque mínimo
                        estoque_min = st.session_state.estoque_min_map.get(item, 0) # Estoque mínimo
                        estoque = st.session_state.estoque_map.get(item, 0) # Estoque atual
                        necessario = int(estoque_min) - int(estoque) # Quantidade necessária para completar o estoque mínimo
                        st.caption(":red[Necessário {} para completar o estoque MÍNIMO.]".format(necessario))
                    with col5:  
                        
                        # Alocação de quantidade desejada de compra
                        st.number_input("", min_value=0, step=1, value=0, key=f"slider_{item}")
                    st.write('---')
                
                enviado = st.form_submit_button("Atualizar e Enviar Selecionados")

            # Caso o botão seja acionado e tenha checkbox marcada, enviaremos o pedido para a tabela de necessidades, este, por sua vez, chegará nela como pedido pendente
            if enviado:
                
                itens_para_mover = []

                for item in lote_atual:
                    
                    # Pegamos as chaves dinâmicas
                    chave_checkbox = f"check_{item}"
                    chave_slider = f"slider_{item}"
                    chave_obs = f"obs_{item}"
                    
                    # Verificamos se a checkbox foi marcada
                    if st.session_state[chave_checkbox]:
                        # Guardamos os dados
                        quantidade = st.session_state[chave_slider]
                        observacoes = st.session_state.get(chave_obs, "")

                        itens_para_mover.append([
                            item,
                            quantidade,
                            observacoes
                        ])
                        # Deletamos as chaves para resetar o formulário
                        del st.session_state[chave_checkbox]
                        del st.session_state[chave_slider]
                
                if itens_para_mover:
                    # Reseta a barra de busca
                    st.session_state.reset_input_busca = True
                    # Adiciona os itens à lista de pedidos, como também a observação, se houver
                    compra_item(itens_para_mover)
                    
                    logger_info.info(f"Itens {', '.join([f'{x[0]} (qtd: {x[1]})' for x in itens_para_mover])} adicionados à tabela de necessidades no banco de dados.")

                    """ nomes_para_remover = [x[0] for x in itens_para_mover]
                    st.session_state.necessidades = [
                        x for x in st.session_state.necessidades
                        if x not in nomes_para_remover
                    ]
                        """
                    
                    st.session_state.dataload = 0 # Força recarga da lista de necessidades
                    st.session_state.pagina_atual = 0 # Reseta a página para a primeira
                    st.rerun()
                else:
                    st.warning("Selecione pelo menos um item antes de enviar.")

            # Paginação da tabela de seleção de compra
            col_ant, col_meio, col_prox = st.columns([1, 9.3, 1])
            num_pag_total = (total_itens + ITENS_POR_PAGINA - 1) // ITENS_POR_PAGINA


            if st.session_state.pagina_atual + 1 != 1:
                with col_meio:
                    st.markdown(f"**Página {st.session_state.pagina_atual + 1}-{num_pag_total}**")

            else:
                with col_ant:
                    st.markdown(f"**Página {st.session_state.pagina_atual + 1}-{num_pag_total}**")

            if st.session_state.pagina_atual + 1 != 1:
                with col_ant:
                    if st.button("Anterior", icon=":material/line_start_arrow_notch:", width="stretch", key="button_ant_disp"):
                        if st.session_state.pagina_atual > 0:
                            st.session_state.pagina_atual -= 1
                            st.rerun()

            if st.session_state.pagina_atual + 1 != num_pag_total:
                with col_prox:

                    # Só mostra o botão próximo se houver mais itens na frente
                    if fim < total_itens:
                        if st.button("Próximo", icon=":material/line_end_arrow_notch:", width="stretch", key="button_pos_disp"):
                            st.session_state.pagina_atual += 1
                            st.rerun()

    # Medição do tempo de execução do script
    end_time = time.time()

    # Log do tempo de execução
    logger_info.info(f"tempo de execução do script: {end_time - start_time:.2f} segundos")

# Fim do bloco de autenticação
elif st.session_state["authentication_status"] is False:
    st.error('Usuário/senha incorreto')
# Caso o usuário ainda não tenha inserido as credenciais
elif st.session_state["authentication_status"] is None:
    st.warning('Por favor, insira seu usuário e senha')