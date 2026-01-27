import streamlit as st
import json
import os
import streamlit_authenticator as st_auth
import yaml
from yaml.loader import SafeLoader

# INTERFACE DO USUÁRIO
st.set_page_config(page_title="CaldMAN/Gerenciar Taxonomia", layout="wide")

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

    st.sidebar.info("Gerenciamento de Taxonomia:\nEdite e delete famílias, tipos, variações e especificações.")

    st.sidebar.markdown("---")

    from dotenv import load_dotenv
    load_dotenv()
    email_dev = os.getenv("EMAIL_DEV")
    
    st.sidebar.write("Para mais informações, entre em contato com o desenvolvedor:")
    st.sidebar.caption(f"e-mail:\n{email_dev}")

    # CONFIGURAÇÃO DE DADOS
    FILE_TAXONOMIA = "taxonomia_materiais.json"

    def carregar_taxonomia():
        if not os.path.exists(FILE_TAXONOMIA):
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
        with open(FILE_TAXONOMIA, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    #Configurações manuais de CSS da página
    @st.cache_data
    def inject_css():
        with open("custom/style.css") as file:
            st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)
        return

    # Injeção do CSS personalizado
    inject_css()

    # Título da página
    st.write("# Gerenciar Taxonomia de Materiais")
    st.markdown("Edite, renomeie ou delete famílias, tipos, variações e especificações técnicas.")

    # Carrega dados
    taxonomia = carregar_taxonomia()

    # Criar abas para cada seção
    tab1, tab2, tab3, tab4 = st.tabs(["👨‍👩‍👧 Famílias", "🏷️ Tipos", "✨ Variações", "📋 Especificações"])

    # GERENCIAR FAMÍLIAS
    with tab1:
        st.subheader("Gerenciar Famílias")
        
        familias = list(taxonomia.keys())
        
        if not familias:
            st.info("Nenhuma família cadastrada.")
        else:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                familia_selecionada = st.selectbox("Selecione uma família para editar ou deletar", familias, key="familia_select")
            
            with col2:
                st.write("")
                st.write("")
                st.write("**Ações:**")
            
            col_edit, col_delete = st.columns(2)
            
            with col_edit:
                if st.button("✏️ Editar Nome", key="btn_edit_familia"):
                    st.session_state['edit_familia'] = True
            
            with col_delete:
                if st.button("🗑️ Deletar Família", key="btn_delete_familia"):
                    st.session_state['confirm_delete_familia'] = True
            
            # Modo de edição
            if st.session_state.get('edit_familia'):
                novo_nome = st.text_input("Novo nome da família:", value=familia_selecionada, key="input_edit_familia").upper()
                
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.button("✅ Salvar", key="save_edit_familia"):
                        if novo_nome and novo_nome != familia_selecionada:
                            if novo_nome not in taxonomia:
                                taxonomia[novo_nome] = taxonomia.pop(familia_selecionada)
                                salvar_taxonomia(taxonomia)
                                st.session_state['edit_familia'] = False
                                st.success(f"Família renomeada para '{novo_nome}'")
                                st.rerun()
                            else:
                                st.error("Já existe uma família com este nome!")
                        else:
                            st.error("Digite um novo nome diferente!")
                
                with col_cancel:
                    if st.button("❌ Cancelar", key="cancel_edit_familia"):
                        st.session_state['edit_familia'] = False
                        st.rerun()
            
            # Confirmação de deleção
            if st.session_state.get('confirm_delete_familia'):
                st.warning(f"⚠️ Tem certeza que deseja deletar a família '{familia_selecionada}'? Todos os tipos e variações também serão deletados!")
                
                col_confirm, col_cancel = st.columns(2)
                with col_confirm:
                    if st.button("🗑️ Confirmar Deleção", key="confirm_delete_familia_btn"):
                        del taxonomia[familia_selecionada]
                        salvar_taxonomia(taxonomia)
                        st.session_state['confirm_delete_familia'] = False
                        st.success(f"Família '{familia_selecionada}' deletada com sucesso!")
                        st.rerun()
                
                with col_cancel:
                    if st.button("❌ Cancelar", key="cancel_delete_familia"):
                        st.session_state['confirm_delete_familia'] = False
                        st.rerun()
    
    # GERENCIAR TIPOS
    with tab2:
        st.subheader("Gerenciar Tipos (Modificadores)")
        
        familias = list(taxonomia.keys())
        
        if not familias:
            st.info("Nenhuma família cadastrada.")
        else:
            familia_selecionada = st.selectbox("Selecione uma família", familias, key="familia_select_tipos")
            
            tipos = list(taxonomia[familia_selecionada]["modificadores"].keys())
            
            if not tipos:
                st.info(f"Nenhum tipo cadastrado para a família '{familia_selecionada}'.")
            else:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    tipo_selecionado = st.selectbox("Selecione um tipo para editar ou deletar", tipos, key="tipo_select")
                
                with col2:
                    st.write("")
                    st.write("")
                    st.write("**Ações:**")
                
                col_edit, col_delete = st.columns(2)
                
                with col_edit:
                    if st.button("✏️ Editar Nome", key="btn_edit_tipo"):
                        st.session_state['edit_tipo'] = True
                
                with col_delete:
                    if st.button("🗑️ Deletar Tipo", key="btn_delete_tipo"):
                        st.session_state['confirm_delete_tipo'] = True
                
                # Modo de edição
                if st.session_state.get('edit_tipo'):
                    novo_nome = st.text_input("Novo nome do tipo:", value=tipo_selecionado, key="input_edit_tipo").upper()
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("✅ Salvar", key="save_edit_tipo"):
                            if novo_nome and novo_nome != tipo_selecionado:
                                if novo_nome not in taxonomia[familia_selecionada]["modificadores"]:
                                    taxonomia[familia_selecionada]["modificadores"][novo_nome] = taxonomia[familia_selecionada]["modificadores"].pop(tipo_selecionado)
                                    salvar_taxonomia(taxonomia)
                                    st.session_state['edit_tipo'] = False
                                    st.success(f"Tipo renomeado para '{novo_nome}'")
                                    st.rerun()
                                else:
                                    st.error("Já existe um tipo com este nome nesta família!")
                            else:
                                st.error("Digite um novo nome diferente!")
                    
                    with col_cancel:
                        if st.button("❌ Cancelar", key="cancel_edit_tipo"):
                            st.session_state['edit_tipo'] = False
                            st.rerun()
                
                # Confirmação de deleção
                if st.session_state.get('confirm_delete_tipo'):
                    st.warning(f"⚠️ Tem certeza que deseja deletar o tipo '{tipo_selecionado}'? Todas as variações também serão deletadas!")
                    
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("🗑️ Confirmar Deleção", key="confirm_delete_tipo_btn"):
                            del taxonomia[familia_selecionada]["modificadores"][tipo_selecionado]
                            salvar_taxonomia(taxonomia)
                            st.session_state['confirm_delete_tipo'] = False
                            st.success(f"Tipo '{tipo_selecionado}' deletado com sucesso!")
                            st.rerun()
                    
                    with col_cancel:
                        if st.button("❌ Cancelar", key="cancel_delete_tipo"):
                            st.session_state['confirm_delete_tipo'] = False
                            st.rerun()
    
    # GERENCIAR VARIAÇÕES
    with tab3:
        st.subheader("Gerenciar Variações")
        
        familias = list(taxonomia.keys())
        
        if not familias:
            st.info("Nenhuma família cadastrada.")
        else:
            familia_selecionada = st.selectbox("Selecione uma família", familias, key="familia_select_var")
            
            tipos = list(taxonomia[familia_selecionada]["modificadores"].keys())
            
            if not tipos:
                st.info(f"Nenhum tipo cadastrado para a família '{familia_selecionada}'.")
            else:
                tipo_selecionado = st.selectbox("Selecione um tipo", tipos, key="tipo_select_var")
                
                variacoes = taxonomia[familia_selecionada]["modificadores"][tipo_selecionado].get("variacoes", [])
                
                if not variacoes:
                    st.info(f"Nenhuma variação cadastrada para o tipo '{tipo_selecionado}'.")
                else:
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        variacao_selecionada = st.selectbox("Selecione uma variação para editar ou deletar", variacoes, key="var_select")
                    
                    with col2:
                        st.write("")
                        st.write("")
                        st.write("**Ações:**")
                    
                    col_edit, col_delete = st.columns(2)
                    
                    with col_edit:
                        if st.button("✏️ Editar Nome", key="btn_edit_var"):
                            st.session_state['edit_var'] = True
                    
                    with col_delete:
                        if st.button("🗑️ Deletar Variação", key="btn_delete_var"):
                            st.session_state['confirm_delete_var'] = True
                    
                    # Modo de edição
                    if st.session_state.get('edit_var'):
                        novo_nome = st.text_input("Novo nome da variação:", value=variacao_selecionada, key="input_edit_var").upper()
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.button("✅ Salvar", key="save_edit_var"):
                                if novo_nome and novo_nome != variacao_selecionada:
                                    if novo_nome not in variacoes:
                                        idx = variacoes.index(variacao_selecionada)
                                        variacoes[idx] = novo_nome
                                        taxonomia[familia_selecionada]["modificadores"][tipo_selecionado]["variacoes"] = variacoes
                                        salvar_taxonomia(taxonomia)
                                        st.session_state['edit_var'] = False
                                        st.success(f"Variação renomeada para '{novo_nome}'")
                                        st.rerun()
                                    else:
                                        st.error("Já existe uma variação com este nome!")
                                else:
                                    st.error("Digite um novo nome diferente!")
                        
                        with col_cancel:
                            if st.button("❌ Cancelar", key="cancel_edit_var"):
                                st.session_state['edit_var'] = False
                                st.rerun()
                    
                    # Confirmação de deleção
                    if st.session_state.get('confirm_delete_var'):
                        st.warning(f"⚠️ Tem certeza que deseja deletar a variação '{variacao_selecionada}'?")
                        
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("🗑️ Confirmar Deleção", key="confirm_delete_var_btn"):
                                variacoes.remove(variacao_selecionada)
                                taxonomia[familia_selecionada]["modificadores"][tipo_selecionado]["variacoes"] = variacoes
                                salvar_taxonomia(taxonomia)
                                st.session_state['confirm_delete_var'] = False
                                st.success(f"Variação '{variacao_selecionada}' deletada com sucesso!")
                                st.rerun()
                        
                        with col_cancel:
                            if st.button("❌ Cancelar", key="cancel_delete_var"):
                                st.session_state['confirm_delete_var'] = False
                                st.rerun()
    
    # GERENCIAR ESPECIFICAÇÕES
    with tab4:
        st.subheader("Gerenciar Especificações Técnicas")
        
        familias = list(taxonomia.keys())
        
        if not familias:
            st.info("Nenhuma família cadastrada.")
        else:
            familia_selecionada = st.selectbox("Selecione uma família", familias, key="familia_select_specs")
            
            tipos = list(taxonomia[familia_selecionada]["modificadores"].keys())
            
            if not tipos:
                st.info(f"Nenhum tipo cadastrado para a família '{familia_selecionada}'.")
            else:
                tipo_selecionado = st.selectbox("Selecione um tipo", tipos, key="tipo_select_specs")
                
                specs = taxonomia[familia_selecionada]["modificadores"][tipo_selecionado].get("specs", [])
                
                if not specs:
                    st.info(f"Nenhuma especificação cadastrada para o tipo '{tipo_selecionado}'.")
                else:
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        spec_selecionada = st.selectbox("Selecione uma especificação para editar ou deletar", specs, key="spec_select")
                    
                    with col2:
                        st.write("")
                        st.write("")
                        st.write("**Ações:**")
                    
                    col_edit, col_delete = st.columns(2)
                    
                    with col_edit:
                        if st.button("✏️ Editar Nome", key="btn_edit_spec"):
                            st.session_state['edit_spec'] = True
                    
                    with col_delete:
                        if st.button("🗑️ Deletar Especificação", key="btn_delete_spec"):
                            st.session_state['confirm_delete_spec'] = True
                    
                    # Modo de edição
                    if st.session_state.get('edit_spec'):
                        novo_nome = st.text_input("Novo nome da especificação:", value=spec_selecionada, key="input_edit_spec").upper()
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.button("✅ Salvar", key="save_edit_spec"):
                                if novo_nome and novo_nome != spec_selecionada:
                                    if novo_nome not in specs:
                                        idx = specs.index(spec_selecionada)
                                        specs[idx] = novo_nome
                                        taxonomia[familia_selecionada]["modificadores"][tipo_selecionado]["specs"] = specs
                                        salvar_taxonomia(taxonomia)
                                        st.session_state['edit_spec'] = False
                                        st.success(f"Especificação renomeada para '{novo_nome}'")
                                        st.rerun()
                                    else:
                                        st.error("Já existe uma especificação com este nome!")
                                else:
                                    st.error("Digite um novo nome diferente!")
                        
                        with col_cancel:
                            if st.button("❌ Cancelar", key="cancel_edit_spec"):
                                st.session_state['edit_spec'] = False
                                st.rerun()
                    
                    # Confirmação de deleção
                    if st.session_state.get('confirm_delete_spec'):
                        st.warning(f"⚠️ Tem certeza que deseja deletar a especificação '{spec_selecionada}'?")
                        
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("🗑️ Confirmar Deleção", key="confirm_delete_spec_btn"):
                                specs.remove(spec_selecionada)
                                taxonomia[familia_selecionada]["modificadores"][tipo_selecionado]["specs"] = specs
                                salvar_taxonomia(taxonomia)
                                st.session_state['confirm_delete_spec'] = False
                                st.success(f"Especificação '{spec_selecionada}' deletada com sucesso!")
                                st.rerun()
                        
                        with col_cancel:
                            if st.button("❌ Cancelar", key="cancel_delete_spec"):
                                st.session_state['confirm_delete_spec'] = False
                                st.rerun()

elif st.session_state["authentication_status"] is False:
    st.error('Usuário ou senha inválidos')
elif st.session_state["authentication_status"] is None:
    st.warning('Por favor, insira seu usuário e senha')
