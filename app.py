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
    df_u = banco.listar_usuarios()
    st.dataframe(df_u, use_container_width=True)
    
    col_a, col_b, col_c = st.columns(3)
    u_lista = df_u['usuario'].tolist()
    
    with col_a:
        st.subheader("Mudar Senha")
        u_pw = st.selectbox("Usuário:", u_lista, key="u_pw")
        n_pw = st.text_input("Senha:", type="password", key="n_pw")
        if st.button("Confirmar Senha"):
            banco.alterar_senha_usuario(u_pw, n_pw)
            st.success("Senha alterada!")

    with col_b:
        st.subheader("Mudar Cargo")
        u_rl = st.selectbox("Usuário:", u_lista, key="u_rl")
        n_rl = st.radio("Nível:", ["user", "admin"], key="n_rl")
        if st.button("Confirmar Nível"):
            if banco.alterar_nivel_usuario(u_rl, n_rl): st.rerun()

    with col_c:
        st.subheader("Remover")
        lista_del = [u for u in u_lista if u.lower().strip() != 'vitim']
        if lista_del:
            u_del = st.selectbox("Deletar:", lista_del, key="u_del")
            if st.button("Confirmar Exclusão", type="primary"):
                # A CORREÇÃO: Deleta e força o rerun imediatamente
                if banco.deletar_usuario(u_del):
                    st.rerun() 
        else:
            st.info("Apenas seu usuário resta.")
