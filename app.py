import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

# 1. Configuração da Página
st.set_page_config(page_title="Finanças Privadas", page_icon="🔒", layout="wide")

# 2. Iniciar Banco de Dados
banco.criar_tabelas()

# 3. Estado da Sessão
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = ""
    st.session_state.role = ""

# --- LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Acesso Seguro")
    u = st.text_input("Utilizador")
    p = st.text_input("Palavra-passe", type="password")
    if st.button("Entrar", use_container_width=True):
        role = banco.validar_login(u, p)
        if role:
            st.session_state.logado = True
            st.session_state.user = u
            st.session_state.role = role
            st.rerun()
        else:
            st.error("Credenciais incorretas.")
    st.stop()

# --- SIDEBAR (MENU LATERAL) ---
st.sidebar.title(f"👤 {st.session_state.user.upper()}")

# Menu dinâmico com trava de segurança
menu = ["📊 Dashboard Pessoal", "💸 Lançar Gasto"]
if st.session_state.role == 'admin':
    menu.append("👥 Gestão de Utilizadores")

escolha = st.sidebar.selectbox("Navegação:", menu)

st.sidebar.divider()
if st.sidebar.button("Sair", use_container_width=True):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---

if escolha == "💸 Lançar Gasto":
    st.header("💸 Registar Novo Gasto")
    with st.form("form_gasto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        dt = col1.date_input("Data", format="DD/MM/YYYY")
        ct = col2.selectbox("Categoria", ["Alimentação", "Casa", "Lazer", "Saúde", "Transporte", "Outros"])
        ds = st.text_input("Descrição")
        vl = st.number_input("Valor (€)", min_value=0.0, step=0.01)
        
        if st.form_submit_button("Guardar", use_container_width=True):
            if ds and vl > 0:
                banco.salvar_gasto(st.session_state.user, dt, ct, ds, vl)
                st.success("Gasto guardado com privacidade!")
            else:
                st.warning("Preencha a descrição e o valor.")

elif escolha == "👥 Gestão de Utilizadores":
    st.header("👥 Criar Novos Acessos")
    with st.expander("➕ Novo Utilizador"):
        nu = st.text_input("Nome de utilizador")
        np = st.text_input("Definir palavra-passe", type="password")
        nr = st.radio("Tipo de conta", ["user", "admin"], horizontal=True)
        if st.button("Criar Conta"):
            if nu and np:
                if banco.adicionar_usuario(nu, np, nr):
                    st.success(f"Utilizador {nu} criado com sucesso!")
                else:
                    st.error("Erro: Este nome já existe.")

else: # DASHBOARD PESSOAL
    st.header("📊 O Meu Resumo")
    # Busca apenas dados do utilizador logado
    df = banco.buscar_gastos(st.session_state.user, st.session_state.role)
    
    if not df.empty:
        c1, c2 = st.columns(2)
        c1.metric("Total Gasto", f"{df['valor'].sum():.2f} €")
        c2.metric("Lançamentos", len(df))
        
        st.divider()
        df_pizza = df.groupby("categoria")["valor"].sum().reset_index()
        fig = px.pie(df_pizza, values='valor', names='categoria', hole=0.4, title="Meus Gastos por Categoria")
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📂 Ver Histórico Privado"):
            st.dataframe(df.sort_values(by="data", ascending=False), use_container_width=True)
    else:
        st.info("Ainda não tens gastos registados. Começa no menu 'Lançar Gasto'!")
