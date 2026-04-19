import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

# 1. Configuração da Página (Deve ser a primeira coisa)
st.set_page_config(page_title="Finanças Pro", page_icon="💰", layout="wide")

# 2. Garante que o Banco de Dados e Tabelas existam antes de tudo
banco.criar_tabelas()

# 3. Estado da Sessão
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = ""
    st.session_state.role = ""

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Acesso ao Sistema")
    with st.container():
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
                st.error("Usuário ou senha incorretos")
    st.stop()

# --- MENU LATERAL ---
st.sidebar.title(f"👤 {st.session_state.user.upper()}")
menu = ["📊 Resumo", "💸 Novo Gasto"]
if st.session_state.role == 'admin':
    menu.append("👥 Gerenciar Usuários")

escolha = st.sidebar.selectbox("Navegação", menu)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- LÓGICA DAS TELAS ---
if escolha == "💸 Novo Gasto":
    st.header("Registrar Novo Gasto")
    with st.form("form_gasto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        data = col1.date_input("Data")
        cat = col2.selectbox("Categoria", ["Mercado", "Lazer", "Contas Fixas", "Saúde", "Transporte", "Outros"])
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        
        if st.form_submit_button("Salvar Gasto", use_container_width=True):
            if desc and valor > 0:
                banco.salvar_gasto(st.session_state.user, data, cat, desc, valor)
                st.success("Gasto registrado!")
            else:
                st.warning("Preencha todos os campos corretamente.")

elif escolha == "👥 Gerenciar Usuários":
    st.header("Painel do Administrador")
    with st.expander("Criar Novo Usuário"):
        n_u = st.text_input("Login")
        n_p = st.text_input("Senha", type="password")
        if st.button("Cadastrar"):
            if banco.adicionar_usuario(n_u, n_p, 'user'):
                st.success("Usuário criado!")
            else:
                st.error("Erro ou usuário já existe.")

else: # TELA RESUMO
    st.header("📊 Painel de Controle")
    df = banco.buscar_gastos(st.session_state.user, st.session_state.role)
    
    if not df.empty:
        c1, c2 = st.columns(2)
        c1.metric("Total Gasto", f"R$ {df['valor'].sum():.2f}")
        c2.metric("Total de Registros", len(df))
        
        st.divider()
        
        # Gráfico
        df_pizza = df.groupby("categoria")["valor"].sum().reset_index()
        fig = px.pie(df_pizza, values='valor', names='categoria', hole=0.4, title="Gastos por Categoria")
        st.plotly_chart(fig, use_container_width=True)
        
        # Histórico
        with st.expander("Ver Histórico Completo"):
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Planilha (CSV)", data=csv, file_name="meus_gastos.csv", mime="text/csv")
    else:
        st.info("Ainda não há dados registrados.")
