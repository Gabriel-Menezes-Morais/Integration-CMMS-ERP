import os
import streamlit as st
from funcoesBD import compra_item, deletar_item_carrinho, carrinho_full_filtrado
from integracao import extract
from listas import listagem_nec, listagem_ped
import time
import json
from logging.config import dictConfig
import logging
from dotenv import load_dotenv

load_dotenv()

imagem = os.getenv("IMAGE")
    
with open("log_config.json", "r") as f:
    config = json.load(f)

logging.config.dictConfig(config)

logger_info = logging.getLogger("app.lowlevel")

st.set_page_config(layout="wide")

if "enviado" not in st.session_state:
    st.session_state.enviado = 0

if st.session_state.enviado == 1:
    placeholder = st.empty()

    placeholder.info("Pedido realizado.")
    
    time.sleep(2)

    placeholder.empty()
    st.session_state.enviado -= 1
elif st.session_state.enviado == 2:
    placeholder = st.empty()

    placeholder.info("Pedido desfeito.")

    time.sleep(2)

    placeholder.empty()
    st.session_state.enviado -= 2
   

#Configurações manuais de CSS da página
with open("style.css") as file:
    st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)

collogo, coltitle, colspace = st.columns([0.1, 0.7, 0.1])
with coltitle:
    st.write("""
        # Geração de Necessidade
    """)
with collogo:
    st.image(imagem, width=250)
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

df_check = st.session_state.extract

if 'df' not in st.session_state: 

    necessidades = listagem_nec()
    st.session_state.necessidades = necessidades
    st.session_state.df = carrinho_full_filtrado()

df_pedidos = st.session_state.df

ITENS_POR_PAGINA_NEC = 5

if 'pagina_atual_nec' not in st.session_state:
    st.session_state.pagina_atual_nec = 0

def resetar_pagina():
    st.session_state.pagina_atual_nec = 0

# Filtragem para selecionar necessidades específicas

col_pag, col_fil = st.columns([0.78, 0.219])

with col_fil:
    filtro = st.radio(
        "FILTRO",
        ["Pendentes", "Concluídos", "Todos"],
        horizontal=True
    )

if filtro == "Concluídos":
    df_pedidos = df_pedidos[df_pedidos['IDPedCom'].notna()]
elif filtro == "Pendentes":
    df_pedidos = df_pedidos[df_pedidos['IDPedCom'].isna()]

if 'pedidos' not in st.session_state:
    st.session_state.pedidos = listagem_ped(df_pedidos)

total_itens_nec = len(st.session_state.pedidos)

# Cálculos dos índices (Onde começa e onde termina a fatia)
inicio_nec = st.session_state.pagina_atual_nec * ITENS_POR_PAGINA_NEC
fim_nec = inicio_nec + ITENS_POR_PAGINA_NEC

# Cria a sub-lista (Apenas os 5 itens da vez)
lote_atual_nec = st.session_state.pedidos[inicio_nec:fim_nec]


with col_pag:
# Mostra em qual página estamos
    st.caption(f"Mostrando {len(lote_atual_nec)} de {total_itens_nec} itens encontrados.")

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
        resetar_pagina()

    lista_filtrada_nec = []

    if not termo_busca_nec:
        lista_filtrada_nec = lote_atual_nec
    else:
        termo_nec = termo_busca_nec.lower()
        logger_info.info(f"Usuário pesquisou por '{termo_busca_nec}' na lista de necessidades.")
        for item_id, item in lote_atual_nec:
            # Busca a descrição no DataFrame
            desc_raw = df_check.loc[df_check['Cód. Interno'] == item_id, "Descrição"]
            descricao = str(desc_raw.values[0]) if not desc_raw.empty else ""
            
            # Verifica se o termo está no ID (convertido p/ texto) OU na Descrição
            if termo_nec in str(item_id) or termo_nec in descricao.lower():
                lista_filtrada_nec.append((item_id, item))

if not df_pedidos.empty:

    # Tabela de amostragem das necessidades geradas
    with st.form("carrinho"):
        for id, item_comprado in enumerate(lista_filtrada_nec):

            col1, col2, col3, col4 = st.columns([0.5, 0.166, 0.166, 0.166])

            pendencia = 'pendente'
            verif = df_pedidos['IDPedCom'].loc[df_pedidos['CodProCOPY'] == item_comprado[0]]
            exist = (df_pedidos['CodProCOPY'] ==  item_comprado[0]).any()

            # Verifica se o pedido foi atendido ou está pendente, caso foi atendido, não terá opção de desfazer o pedido
            if verif.empty and exist:
                pendencia = 'concluído'

            with col1:

                if pendencia == "pendente":

                    item_nome = df_check["Descrição"].loc[df_check['Cód. Interno'] == item_comprado[0]]
                    if isinstance(item_nome, str):
                        st.write("Descrição: {}".format(item_nome))
                    else:
                        item_nome = item_nome.values[0]
                    st.checkbox("Descrição: {}".format(item_nome), key=f"check_{item_comprado[0]}_{id}") 
            with col2:

                st.write("Código do Produto: {}".format(item_comprado[0]))    
            with col3:

                st.write("Quantidade: {:.1f}".format(item_comprado[1]))
            with col4:

                st.write("{}".format(pendencia))
            st.write('---')
        enviado = st.form_submit_button("Desfazer necessidades selecionadas")
    
    # Caso o botão for selecionado e houver itens selecionados na check box, retornaremos para a aba de seleção de compra
    if enviado:
        
        itens_para_mover = []

        for id, i in enumerate(lista_filtrada_nec):

            chave_checkbox = f"check_{i[0]}_{id}"

            if st.session_state[chave_checkbox]:

                itens_para_mover.append(i[0])
                del st.session_state[chave_checkbox]
        # Caso houver itens, retornaremos o item para a lista de necessidades e atualizaremos a tabela do Banco de dados
        if itens_para_mover:

            st.session_state.reset_input_busca_nec = True

            st.session_state.necessidades.extend(itens_para_mover)
            deletar_item_carrinho(itens_para_mover)
            
            logger_info.info(f"Itens {', '.join([f'{x}' for x in itens_para_mover])} removidos da tabela de necessidades no banco de dados.")
            ids_para_remover = itens_para_mover 

            st.session_state.pedidos = [
                x for x in st.session_state.pedidos
                if [x[0]] not in ids_para_remover  
            ]

            logger_info.info(f"Itens {', '.join([f'{x}' for x in itens_para_mover])} removidos da tabela de necessidades no banco de dados.")
            st.session_state.enviado += 2
            st.rerun()
        else:
            st.warning("Selecione pelo menos um item antes de enviar.")
    col_ant, col_meio, col_prox = st.columns([1, 9.3, 1])

    num_pag_total_nec = 1

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

ITENS_POR_PAGINA = 5

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

    if termo_busca:
        resetar_pagina()
    
    lista_filtrada = []

    if not termo_busca:
        lista_filtrada = st.session_state.necessidades
    else:
        termo = termo_busca.lower()
        logger_info.info(f"Usuário pesquisou por '{termo_busca}' na lista de necessidades.")
        for item_id in st.session_state.necessidades:
            # Busca a descrição no DataFrame
            desc_raw = df_check.loc[df_check['Cód. Interno'] == item_id, "Descrição"]
            descricao = str(desc_raw.values[0]) if not desc_raw.empty else ""
            
            # Verifica se o termo está no ID (convertido p/ texto) OU na Descrição
            if termo in str(item_id) or termo in descricao.lower():
                lista_filtrada.append(item_id)

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

        with st.form("Meu formulário de compras"):
            for item in lote_atual:

                col1, col2, col3 = st.columns([0.5, 0.3, 0.2])

                with col1:
                    
                    # Verificação para caso houver mais de um item com o mesmo Código Interno, por alguma falha externa
                    item_nome = df_check["Descrição"].loc[df_check['Cód. Interno'] == item]
                    if isinstance(item_nome, str):
                        continue
                    else:
                        item_nome = item_nome.values[0]
                    st.checkbox(item_nome, key=f"check_{item}")
                with col2:

                    st.write("Código do Produto: {}".format(item))
                with col3:  
                    
                    # Alocação de quantidade desejada de compra
                    st.number_input("", min_value=0, step=1, value=0, key=f"slider_{item}")
                st.write('---')
            
            enviado = st.form_submit_button("Atualizar e Enviar Selecionados")

        # Caso o botão seja acionado e tenha checkbox marcada, enviaremos o pedido para a tabela de necessidades, este, por sua vez, chegará nela como pedido pendente
        if enviado:
            
            itens_para_mover = []

            for i in lote_atual:

                chave_checkbox = f"check_{i}"
                chave_slider = f"slider_{i}"

                if st.session_state[chave_checkbox]:
                    # Guardamos os dados
                    quantidade = st.session_state[chave_slider]
                    
                    itens_para_mover.append([
                        i,
                        quantidade
                    ])

                    del st.session_state[chave_checkbox]
                    del st.session_state[chave_slider]
            
            if itens_para_mover:
                
                st.session_state.reset_input_busca = True

                st.session_state.pedidos.extend(itens_para_mover)
                compra_item(itens_para_mover)
                
                logger_info.info(f"Itens {', '.join([f'{x[0]} (qtd: {x[1]})' for x in itens_para_mover])} adicionados à tabela de necessidades no banco de dados.")

                nomes_para_remover = [x[0] for x in itens_para_mover]
                st.session_state.necessidades = [
                    x for x in st.session_state.necessidades
                    if x not in nomes_para_remover
                ]
                
                st.session_state.enviado += 1
                st.rerun()
            else:
                st.warning("Selecione pelo menos um item antes de enviar.")
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