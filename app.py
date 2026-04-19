import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

# 1. Configuração da Página
st.set_page_config(page_title="Gestão Financeira", page_icon="💰", layout="wide")

# 2. Iniciar Banco
banco.criar_tabelas()

# 3. Controle de Login
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = ""
    st.session_state.role = ""

if not st.session_state.logado:
    st.title("🔐 Acesso Restrito")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar", use_container_width=True):
        role = banco.validar_login(u, p)
        if role:
            st.session_state.logado = True
            st.session_state.user = u
            st.session_state.role = role
            st.rerun()
        else:
            st.error("Dados incorretos!")
    st.stop()

# --- MENU LATERAL COM TRAVA DE SEGURANÇA ---
st.sidebar.title(f"👤 {st.session_state.user.upper()}")

# Lista base (para todos)
menu = ["📊 Dashboard", "💸 Lançar Gastos"]

# SE for admin, adiciona a opção de usuários
if st.session_state.role == 'admin':
    menu.append("👥 Gerenciar Usuários")

escolha = st.sidebar.selectbox("Escolha uma opção:", menu)

st.sidebar.divider()
if st.sidebar.button("Sair", use_container_width=True):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---

if escolha == "💸 Lançar Gastos":
    st.header("💸 Novo Gasto")
    with st.form("form_novo_gasto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        data = col1.date_input("Data", format="DD/MM/YYYY")
        cat = col2.selectbox("Categoria", ["Alimentação", "Transporte", "Fixos", "Lazer", "Saúde", "Outros"])
        desc = st.text_input("O que foi comprado?")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        if st.form_submit_button("Salvar", use_container_width=True):
            if desc and valor > 0:
                banco.salvar_gasto(st.session_state.user, data, cat, desc, valor)
                st.success("Salvo com sucesso!")
            else:
                st.warning("Preencha a descrição e o valor.")

elif escolha == "👥 Gerenciar Usuários":
    st.header("👥 Gestão de Contas")
    with st.expander("Cadastrar Novo Acesso"):
        n_u = st.text_input("Novo Login")
        n_p = st.text_input("Nova Senha", type="password")
        n_r = st.radio("Nível de Acesso", ["user", "admin"], horizontal=True)
        if st.button("Salvar Usuário"):
            if n_u and n_p:
                if banco.adicionar_usuario(n_u, n_p, n_r):
                    st.success(f"Usuário {n_u} criado!")
                else:
                    st.error("Usuário já existe.")

else: # DASHBOARD
    st.header("📊 Painel de Controle")
    df = banco.buscar_gastos(st.session_state.user, st.session_state.role)
    
    if not df.empty:
        c1, c2 = st.columns(2)
        c1.metric("Total Gasto", f"R$ {df['valor'].sum():.2f}")
        c2.metric("Lançamentos", len(df))
        
        st.divider()
        df_p = df.groupby("categoria")["valor"].sum().reset_index()
        fig = px.pie(df_p, values='valor', names='categoria', hole=0.4, title="Divisão por Categoria")
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📂 Histórico"):
            st.dataframe(df.sort_values(by="data", ascending=False), use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exportar CSV", data=csv, file_name="gastos.csv", mime="text/csv")
    else:
        st.info("Lance seu primeiro gasto para ver os gráficos!")
