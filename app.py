import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

# 1. Configuração da Página
st.set_page_config(page_title="Finanças Pro v1.0", page_icon="💰", layout="wide")

# 2. Inicializar Banco
banco.criar_tabelas()

# 3. Controle de Sessão
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = ""
    st.session_state.role = ""

# --- LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Login - Finanças Pro")
    u = st.text_input("Utilizador")
    p = st.text_input("Senha", type="password")
    if st.button("Aceder"):
        role = banco.validar_login(u, p)
        if role:
            st.session_state.logado = True
            st.session_state.user = u
            st.session_state.role = role
            st.rerun()
        else:
            st.error("Incorreto!")
    st.stop()

# --- MENU ---
st.sidebar.title(f"👤 {st.session_state.user.upper()}")
menu = ["📊 Dashboard", "💸 Lançar Gastos"]
if st.session_state.role == 'admin':
    menu.append("👥 Gerenciar Utilizadores")

escolha = st.sidebar.selectbox("Menu", menu)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---
if escolha == "💸 Lançar Gastos":
    st.header("Novo Gasto")
    with st.form("meu_form", clear_on_submit=True):
        data = st.date_input("Data")
        cat = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Saúde", "Fixos", "Outros"])
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("Salvar"):
            banco.salvar_gasto(st.session_state.user, data, cat, desc, valor)
            st.success("Salvo!")

elif escolha == "👥 Gerenciar Utilizadores":
    st.header("Admin")
    novo_u = st.text_input("Novo Usuário")
    novo_p = st.text_input("Senha", type="password")
    if st.button("Criar"):
        if banco.adicionar_usuario(novo_u, novo_p, "user"):
            st.success("Criado!")

else: # DASHBOARD
    st.header("📊 Resumo")
    df = banco.buscar_gastos(st.session_state.user, st.session_state.role)
    
    if not df.empty:
        col1, col2 = st.columns(2)
        col1.metric("Total", f"R$ {df['valor'].sum():.2f}")
        col2.metric("Registros", len(df))
        
        # Gráfico
        df_pizza = df.groupby("categoria")["valor"].sum().reset_index()
        fig = px.pie(df_pizza, values='valor', names='categoria', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela e Download
        with st.expander("Ver Detalhes"):
            st.dataframe(df)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar CSV", data=csv, file_name="gastos.csv", mime="text/csv")
    else:
        st.info("Sem dados.")
