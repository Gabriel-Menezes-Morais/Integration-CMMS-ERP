import os
import streamlit as st
from services.integra_API_Usuarios import list_movest_edit
from database.funcoesBD import compra_item, deletar_item_carrinho, carrinho_full_filtrado
from services.integra_API_ListarPecas import extract
from ETL.listas import listagem_nec, listagem_ped
import json
import logging
from dotenv import load_dotenv
import streamlit_authenticator as st_auth
import pandas as pd
import time
import yaml
from yaml.loader import SafeLoader
from logging.config import dictConfig

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
    st.sidebar.write('Na tabela "SELECIONE OS ITENS" estarão os itens que estão a baixo do estoque mínimo necessário, isto é,' \
    'são necessários para o estoque de manutenção. Para gerar a necessidade do item, marque a caixa ao lado da descrição do item, após isso,' \
    'com a caixa marcada, selecione a quantidade da compra, considerando a unidade do item. Por fim, marque "Atualizar e enviar selecionados".')

    st.sidebar.markdown("--")

    st.sidebar.write("Sobre Desfazer Necessidade")
    st.sidebar.write('Na tabela "NECESSIDADE GERADAS", estarão todos os itens que foram pedidos pelo técnico de manutenção.' \
    'Entre eles, estarão os itens que ja foram comprados pelo setor de compras, marcados como "concluídos", e os itens que ainda não foram, ' \
    'marcados como "pendentes". Para os itens pendentes, ao marcar a caixinha, será desfeito o pedido(certifique com o setor de compras). Posteriormente,' \
    'marque "Aplicar alterações" e desfaça o pedido.')

    st.sidebar.markdown("--")

    st.sidebar.write("Sobre Itens Recebidos")
    st.sidebar.write('Para os itens marcados como concluídos, ao marcar a caixinha, o sistema irá considerar o exato momento de marcação como a hora de recebimento' \
    'e automatizará, marcando como recebido a movimentação de estoque feita no sgman. Assim, aumentando o estoque do item na Lista de Peças. Ao marcar a caixinha,' \
    'selecione "Aplicar alterações.')

    st.sidebar.markdown("--")

    st.sidebar.write('Observação: não selecione itens de diferentes páginas e envie. Faça página por página (caso houver mais de uma).')
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

    st.set_page_config(layout="wide")

    # Função de confirmação de recebimento de itens
    @st.dialog("⚠️ Confirmação Necessária") # Título do modal
    def abrir_confirmacao(chaves_recebidos, itens_recebidos):
        st.write(f"Há itens selecionados como recebido.")
        st.write(f"Você tem certeza do recebimento desse item?")
        st.write("Essa ação não pode ser desfeita.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                if st.button("Sim", type="primary"):# Botão de confirmação
                    for item in itens_recebidos:
                        list_movest_edit(item[0], item[1])
                    logger_info.info("O usuário confirmou o recebimento dos itens.") # Log da confirmação
                    st.rerun()
            except KeyError as e:
                logger_info.info("O usuário marcou novamente um item já recebido") # Log da tentativa de marcar item já recebido
                st.write("O item ja foi marcado como recebido.")
                
        with col2:
            if st.button("Cancelar"):
                
                for item in chaves_recebidos:
                    del item
                st.rerun() # Apenas fecha o modal

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
        st.image(imagem, width=250) 
        pass
    with colspace:
        st.write("")

    col_header, col_button = st.columns([0.89, 0.11])

    # Botão para recarregar os dados baseados nas tabelas externas atualizadas com o ERP 
    with col_header:
        st.write('---')
    with col_button:
        if st.button('recarregar dados'):
            logger_info.info("Usuário recarregou os dados da aplicação.")
            # Lista de chaves que queremos apagar
            chaves_para_limpar = ['extract', 'pedidos', 'necessidades', 'df']
            
            for chave in chaves_para_limpar:
                if chave in st.session_state:
                    del st.session_state[chave]
                
            st.rerun()

    st.subheader("NECESSIDADES GERADAS")

    # Gerenciamento de estado utilizando st.session_state para armazenar as tabelas locais
    if 'extract' not in st.session_state:
        st.session_state.extract = extract()

    # mapas para lookup rápido
    if 'desc_map' not in st.session_state:
        df_check = st.session_state.extract
        st.session_state.desc_map = df_check.set_index('Cód. Interno')['Descrição'].to_dict()
    if 'un_map' not in st.session_state:
        df_check = st.session_state.extract
        st.session_state.un_map = df_check.set_index('Cód. Interno')['Un.'].to_dict()
    if 'estoque_min_map' not in st.session_state:
        df_check = st.session_state.extract
        st.session_state.estoque_min_map = df_check.set_index('Cód. Interno')['Estoque Mín.'].to_dict()
    if 'estoque_map' not in st.session_state:
        df_check = st.session_state.extract
        st.session_state.estoque_map = df_check.set_index('Cód. Interno')['Estoque'].to_dict()

    # Lista de necessidades
    if 'df' not in st.session_state: 

        necessidades = listagem_nec()
        st.session_state.necessidades = necessidades
        st.session_state.df = carrinho_full_filtrado()

    df_pedidos = st.session_state.df

    # Mapa para IDPedCom
    if 'idped_map' not in st.session_state:
        st.session_state.idped_map = df_pedidos.set_index('CodProCOPY')['IDPedCom'].to_dict()

    ITENS_POR_PAGINA_NEC = 3

    if 'pagina_atual_nec' not in st.session_state:
        st.session_state.pagina_atual_nec = 0

    def resetar_pagina_nec():
        st.session_state.pagina_atual_nec = 0

    # Filtragem para selecionar necessidades específicas

    col_pag, col_fil = st.columns([0.78, 0.219])

    with col_fil:
        filtro = st.radio(
            "FILTRO",
            ["Pendentes", "Concluídos", "Todos"],
            horizontal=True
        )

    # Armazena o filtro anterior para comparação
    if 'filtroAnt' not in st.session_state:
        st.session_state.filtroAnt = filtroAnt = 'Todos'
    
    # Aplica o filtro selecionado
    if filtro == "Concluídos":
        df_pedidos = df_pedidos[df_pedidos['IDPedCom'].notna()]
    elif filtro == "Pendentes":
        df_pedidos = df_pedidos[df_pedidos['IDPedCom'].isna()]

    # Atualiza a lista de pedidos se o filtro mudou
    if 'pedidos' not in st.session_state or st.session_state.filtroAnt != filtro:
        st.session_state.pedidos = listagem_ped(df_pedidos)
        st.session_state.filtroAnt = filtro
    total_itens_nec = len(st.session_state.pedidos)

    # Cálculos dos índices (Onde começa e onde termina a fatia)
    inicio_nec = st.session_state.pagina_atual_nec * ITENS_POR_PAGINA_NEC
    fim_nec = inicio_nec + ITENS_POR_PAGINA_NEC

    # Cria a sub-lista (Apenas os 5 itens da vez)
    lote_atual_nec = st.session_state.pedidos[inicio_nec:fim_nec]

    with col_pag:
    # Mostra em qual página estamos
        st.caption(f"Mostrando {len(lote_atual_nec)} de {total_itens_nec} itens encontrados.")

        # Barra de busca para filtrar os itens
        if st.session_state.get("reset_input_busca_nec", False):
            st.session_state["input_busca_nec"] = ""
            st.session_state["reset_input_busca_nec"] = False

        col_busca, col_vazia = st.columns([0.5, 0.5])
        with col_busca:
            termo_busca_nec = st.text_input(
                "🔍 Pesquisar Produto",
                placeholder="Digite o nome ou código...",
                key="input_busca_nec"
            )

        if termo_busca_nec:
            resetar_pagina_nec()

        lista_filtrada_nec = []

        if not termo_busca_nec:
            lista_filtrada_nec = lote_atual_nec
        else:
            termo_nec = termo_busca_nec.lower()
            logger_info.info(f"Usuário pesquisou por '{termo_busca_nec}' na lista de necessidades.")
            lista_filtrada_nec = [
                (item_id, item) for item_id, item in lote_atual_nec
                if termo_nec in str(item_id) or termo_nec in st.session_state.desc_map.get(item_id, "").lower()
            ]

    if not df_pedidos.empty:

        # Tabela de amostragem das necessidades geradas
        with st.form("carrinho"):
            for id, item_comprado in enumerate(lista_filtrada_nec):

                col1, col2, col3, col4, col5 = st.columns([0.3, 0.175, 0.175, 0.175, 0.175])

                # Verificação do status do pedido
                pendencia = 'pendente'
                idped = st.session_state.idped_map.get(item_comprado[0], None)

                if idped is not None and pd.notna(idped):
                    pendencia = 'concluído'

                with col1:
        
                    if pendencia == "pendente":
                        # Item pendente, pode desfazer a necessidade
                        item_nome = st.session_state.desc_map.get(item_comprado[0], "")
                        st.caption(":blue[Desfazer necessidade?]")
                        st.checkbox("Descrição: {}".format(item_nome), key=f"check_{item_comprado[0]}_{id}")
                        
                    else:
                        # Item concluído, pode marcar como recebido
                        item_nome = st.session_state.desc_map.get(item_comprado[0], "")
                        st.caption(":yellow[Item recebido?]")
                        st.checkbox("Descrição: {}".format(
                            item_nome), key=f"recebido_{item_comprado[0]}_{id}")
                        
                with col2:
                    st.write("")
                    st.write("Un.: {}".format(st.session_state.un_map.get(item_comprado[0], ""))) 
                with col3:
                    st.write("")
                    st.write("Cód.: {}".format(item_comprado[0]))    
                with col4:
                    st.write("")
                    st.write("Qtd: {:.1f}".format(item_comprado[1]))
                with col5:
                    st.write("")
                    st.write("{}".format(pendencia))
                st.write('---')

            enviado = st.form_submit_button("Aplicar alterações")
        
        # Caso o botão for selecionado e houver itens selecionados na check box, retornaremos para a aba de seleção de compra
        if enviado:

            itens_para_mover = []
            itens_recebidos = []
            chaves_recebidos = []
            for id, i in enumerate(lista_filtrada_nec):

                chave_checkbox = f"check_{i[0]}_{id}"
                chave_checkbox_rec = f"recebido_{i[0]}_{id}"
                if st.session_state.get(chave_checkbox, False):

                    itens_para_mover.append(i[0])
                    del st.session_state[chave_checkbox]
                if st.session_state.get(chave_checkbox_rec, False):
                    
                    chaves_recebidos.append(st.session_state[chave_checkbox_rec])
                    itens_recebidos.append(i)

            # Caso houver itens, retornaremos o item para a lista de necessidades e atualizaremos a tabela do Banco de dados
            if itens_recebidos:
                
                abrir_confirmacao(chaves_recebidos, itens_recebidos)

            if itens_para_mover:
                # Retorna os itens para a lista de necessidades
                st.session_state.reset_input_busca_nec = True
                # Adiciona os itens de volta à lista de necessidades
                st.session_state.necessidades.extend(itens_para_mover)
                deletar_item_carrinho(itens_para_mover)
                
                logger_info.info(f"Itens {', '.join([f'{x}' for x in itens_para_mover])} removidos da tabela de necessidades no banco de dados.")
                ids_para_remover = itens_para_mover 

                st.session_state.pedidos = [
                    x for x in st.session_state.pedidos
                    if [x[0]] not in ids_para_remover  
                ]

                logger_info.info(f"Itens {', '.join([f'{x}' for x in itens_para_mover])} removidos da tabela de necessidades no banco de dados.")
                st.rerun()
            else:
                if not itens_recebidos:
                    st.warning("Selecione pelo menos um item antes de enviar.")
        
        # Paginação da tabela de necessidades
        col_ant, col_meio, col_prox = st.columns([1, 9.3, 1])

        num_pag_total_nec = 1
        
        # Cálculo do número total de páginas
        if total_itens_nec % 5 != 0:
            num_pag_total_nec = int((total_itens_nec/5 + 1))
        else:
            num_pag_total_nec = int((total_itens_nec/5))

        if st.session_state.pagina_atual_nec + 1 != 1:
            with col_meio:
                st.markdown(f"**Página {st.session_state.pagina_atual_nec + 1}-{num_pag_total_nec}**")
        else:
            with col_ant:
                st.markdown(f"**Página {st.session_state.pagina_atual_nec + 1}-{num_pag_total_nec}**")
        if st.session_state.pagina_atual_nec + 1 != 1:
            with col_ant:
                if st.button("Anterior", icon=":material/line_start_arrow_notch:", width="stretch", key="button_ant_nec"):
                    if st.session_state.pagina_atual_nec > 0:
                        st.session_state.pagina_atual_nec -= 1
                        st.rerun()

        if st.session_state.pagina_atual_nec + 1 != num_pag_total_nec:
            with col_prox:
                # Só mostra o botão próximo se houver mais itens na frente
                if fim_nec < total_itens_nec:
                    if st.button("Próximo", icon=":material/line_end_arrow_notch:", width="stretch", key="button_pos_nec"):
                        st.session_state.pagina_atual_nec += 1
                        st.rerun()
    else:
        if filtro == "Concluídos": 
            st.info("Não há compras concluídas.")
        elif filtro == "Pendentes":
            st.info("Não há compras pendentes.")
        elif filtro == "Todos":
            st.info("Não há necessidades geradas.")

    st.subheader("SELECIONE OS ITENS")

    ITENS_POR_PAGINA = 3

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

        col_busca, col_vazia = st.columns([0.5, 0.5])
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
            st.warning(f"Nenhum produto encontrado para '{termo_busca}'.")
        else:
            total_itens = len(lista_filtrada)
            
            # Cálculos dos índices (Onde começa e onde termina a fatia)
            inicio = st.session_state.pagina_atual * ITENS_POR_PAGINA
            fim = inicio + ITENS_POR_PAGINA
            
            # Cria a sub-lista (Apenas os 5 itens da vez)
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

                for i in lote_atual:
                    
                    # Pegamos as chaves dinâmicas
                    chave_checkbox = f"check_{i}"
                    chave_slider = f"slider_{i}"
                    
                    # Verificamos se a checkbox foi marcada
                    if st.session_state[chave_checkbox]:
                        # Guardamos os dados
                        quantidade = st.session_state[chave_slider]
                        
                        itens_para_mover.append([
                            i,
                            quantidade
                        ])
                        # Deletamos as chaves para resetar o formulário
                        del st.session_state[chave_checkbox]
                        del st.session_state[chave_slider]
                
                if itens_para_mover:
                    # Reseta a barra de busca
                    st.session_state.reset_input_busca = True
                    # Adiciona os itens à lista de pedidos
                    st.session_state.pedidos.extend(itens_para_mover)
                    compra_item(itens_para_mover)
                    
                    logger_info.info(f"Itens {', '.join([f'{x[0]} (qtd: {x[1]})' for x in itens_para_mover])} adicionados à tabela de necessidades no banco de dados.")

                    nomes_para_remover = [x[0] for x in itens_para_mover]
                    st.session_state.necessidades = [
                        x for x in st.session_state.necessidades
                        if x not in nomes_para_remover
                    ]
                    
                    st.rerun()
                else:
                    st.warning("Selecione pelo menos um item antes de enviar.")

            # Paginação da tabela de seleção de compra
            col_ant, col_meio, col_prox = st.columns([1, 9.3, 1])

            num_pag_total = 1

            if total_itens % 5 != 0:
                num_pag_total = int((total_itens/5 + 1))
            else:
                num_pag_total = int((total_itens/5))

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