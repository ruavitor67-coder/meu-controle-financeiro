import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

# 1. Configuração da Página
st.set_page_config(page_title="Meu Controle Financeiro", page_icon="💰", layout="wide")

# 2. Iniciar Banco
banco.criar_tabelas()

# 3. Estado da Sessão
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = ""
    st.session_state.role = ""

# --- LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Acesso ao Sistema")
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
            st.error("Usuário ou senha inválidos.")
    st.stop()

# --- MENU LATERAL ---
st.sidebar.title(f"👤 {st.session_state.user.upper()}")

menu = ["📊 Dashboard", "💸 Lançar Gasto"]
if st.session_state.role == 'admin':
    menu.append("👥 Gerenciar Usuários")

escolha = st.sidebar.selectbox("Navegação:", menu)

st.sidebar.divider()
if st.sidebar.button("Sair", use_container_width=True):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---

if escolha == "💸 Lançar Gasto":
    st.header("💸 Registrar Novo Gasto")
    with st.form("form_gasto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        dt = col1.date_input("Data", format="DD/MM/YYYY")
        ct = col2.selectbox("Categoria", ["Alimentação", "Moradia", "Lazer", "Saúde", "Transporte", "Outros"])
        ds = st.text_input("Descrição")
        vl = st.number_input("Valor (R$)", min_value=0.0, step=0.01) # Atualizado para R$
        
        if st.form_submit_button("Salvar Gasto", use_container_width=True):
            if ds and vl > 0:
                banco.salvar_gasto(st.session_state.user, dt, ct, ds, vl)
                st.success("Gasto salvo com sucesso!")
            else:
                st.warning("Informe a descrição e um valor maior que zero.")

elif escolha == "👥 Gerenciar Usuários":
    st.header("👥 Gestão de Contas")
    with st.expander("➕ Criar Novo Usuário"):
        nu = st.text_input("Nome do usuário")
        np = st.text_input("Definir senha", type="password")
        nr = st.radio("Nível", ["user", "admin"], horizontal=True)
        if st.button("Cadastrar"):
            if nu and np:
                if banco.adicionar_usuario(nu, np, nr):
                    st.success(f"Usuário {nu} criado!")
                else:
                    st.error("Erro: Este nome já está em uso.")

else: # DASHBOARD
    st.header("📊 Resumo de Gastos")
    df = banco.buscar_gastos(st.session_state.user, st.session_state.role)
    
    if not df.empty:
        c1, c2 = st.columns(2)
        # Exibição do total em Reais
        c1.metric("Total Gasto", f"R$ {df['valor'].sum():.2f}")
        c2.metric("Lançamentos", len(df))
        
        st.divider()
        df_pizza = df.groupby("categoria")["valor"].sum().reset_index()
        fig = px.pie(df_pizza, values='valor', names='categoria', hole=0.4, title="Meus Gastos por Categoria")
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📂 Histórico Detalhado"):
            # Ajustando a tabela para exibir R$ também se desejar (opcional no dataframe)
            st.dataframe(df.sort_values(by="data", ascending=False), use_container_width=True)
    else:
        st.info("Você ainda não lançou gastos.")
