import streamlit as st
import pandas as pd
import plotly.express as px
import banco 
from io import BytesIO

def f_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Gestão Financeira", page_icon="💰", layout="wide")
banco.criar_tabelas()

if 'logado' not in st.session_state:
    st.session_state.logado, st.session_state.user, st.session_state.role = False, "", ""
if 'editando_salario' not in st.session_state:
    st.session_state.editando_salario = False

# --- LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        role = banco.validar_login(u, p)
        if role:
            st.session_state.logado, st.session_state.user, st.session_state.role = True, u, role
            st.rerun()
    st.stop()

# --- SIDEBAR ---
st.sidebar.title(f"👤 {st.session_state.user.upper()}")
sal_atual = banco.buscar_salario(st.session_state.user)

# Interface de Salário (Melhoria)
if not st.session_state.editando_salario:
    col_v, col_b = st.sidebar.columns([1.5, 1])
    col_v.write(f"Salário: **{f_moeda(sal_atual)}**")
    if col_b.button("Alterar"):
        st.session_state.editando_salario = True
        st.rerun()
else:
    n_sal = st.sidebar.number_input("Novo Valor:", value=float(sal_atual))
    if st.sidebar.button("Salvar Salário"):
        banco.atualizar_salario(st.session_state.user, n_sal)
        st.session_state.editando_salario = False
        st.rerun()

st.sidebar.divider()
menu = ["📊 Dashboard", "💸 Lançar Gasto", "📥 Importar Extrato", "🎯 Metas"]

# Visibilidade restrita para Vitim ou Admins
if st.session_state.user.lower() == 'vitim' or st.session_state.role == 'admin':
    menu.append("👥 Usuários")

escolha = st.sidebar.selectbox("Navegação:", menu)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---

if escolha == "📊 Dashboard":
    st.header("📊 Painel de Controle")
    df = banco.buscar_gastos(st.session_state.user)
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        st.metric("Total Gasto", f_moeda(df['valor'].sum()))
        st.dataframe(df, use_container_width=True)
        st.plotly_chart(px.pie(df, values='valor', names='categoria', hole=0.4))
    else:
        st.info("Nenhum dado encontrado.")

elif escolha == "💸 Lançar Gasto":
    st.header("💸 Novo Gasto")
    with st.form("gasto"):
        d = st.date_input("Data")
        c = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
        ds = st.text_input("Descrição")
        v = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("Salvar"):
            banco.salvar_gasto(st.session_state.user, d, c, ds, v)
            st.success("Salvo!")

elif escolha == "👥 Usuários":
    st.header("👥 Gestão de Usuários")
    
    # 1. Primeiro pegamos a lista de usuários
    df_u = banco.listar_usuarios()
    u_lista = df_u['usuario'].tolist()
    
    # 2. Criamos as colunas
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.subheader("🔑 Senha")
        u_pw = st.selectbox("Usuário:", u_lista, key="s1")
        n_pw = st.text_input("Nova Senha", type="password", key="s2")
        if st.button("Alterar Senha"):
            banco.alterar_senha_usuario(u_pw, n_pw)
            st.success("Senha alterada!")

    with col_b:
        st.subheader("🛡️ Nível")
        u_rl = st.selectbox("Usuário:", u_lista, key="n1")
        n_rl = st.radio("Nível:", ["user", "admin"], key="n2")
        if st.button("Alterar Nível"):
            banco.alterar_nivel_usuario(u_rl, n_rl)
            st.rerun()

    with col_c:
        st.subheader("🗑️ Remover")
        # Filtramos para não mostrar o seu usuário na lista de deletar
        lista_deletar = [u for u in u_lista if u.lower().strip() != 'vitim']
        
        if lista_deletar:
            u_para_remover = st.selectbox("Escolha:", lista_deletar, key="d1")
            
            # BOTÃO DE EXCLUSÃO
            if st.button("CONFIRMAR EXCLUSÃO", type="primary"):
                # Chamamos a função do banco
                sucesso = banco.deletar_usuario(u_para_remover)
                if sucesso:
                    st.toast(f"Usuário {u_para_remover} excluído!")
                    # O RERUN É OBRIGATÓRIO PARA O ADMIN SUMIR DA TELA
                    st.rerun() 
                else:
                    st.error("Erro ao excluir no banco de dados.")
        else:
            st.info("Só existe o seu usuário.")

    # 3. Mostramos a tabela por último para garantir que ela venha atualizada
    st.divider()
    st.dataframe(df_u, use_container_width=True)
