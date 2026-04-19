import streamlit as st
import pandas as pd
import banco  # <--- Certifique-se de que está importando 'banco' e não 'funcoes'

# Iniciar o banco de dados
banco.criar_tabelas()

st.set_page_config(page_title="Finanças Pro v1.0", layout="wide")

# Gerenciamento de Sessão (Login)
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = ""
    st.session_state.role = ""

if not st.session_state.logado:
    st.title("🔐 Login - Finanças Pro")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Acessar Sistema"):
        role = banco.validar_login(u, p)
        if role:
            st.session_state.logado = True
            st.session_state.user = u
            st.session_state.role = role
            st.rerun()
        else:
            st.error("Dados inválidos!")
    st.stop()

# --- ÁREA LOGADA ---
st.sidebar.title(f"👤 {st.session_state.user.upper()}")
st.sidebar.write(f"Nível: {st.session_state.role}")

menu = ["📊 Dashboard", "💸 Lançar Gastos"]
if st.session_state.role == 'admin':
    menu.append("👥 Gerenciar Usuários")

escolha = st.sidebar.selectbox("Ir para:", menu)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---
if escolha == "💸 Lançar Gastos":
    st.header("Novo Lançamento")
    with st.form("form_gastos", clear_on_submit=True):
        col1, col2 = st.columns(2)
        dt = col1.date_input("Data")
        ct = col2.selectbox("Categoria", ["Alimentação", "Transporte", "Saúde", "Lazer", "Outros"])
        ds = st.text_input("Descrição")
        vl = st.number_input("Valor R$", min_value=0.0)
        if st.form_submit_button("Salvar"):
            banco.salvar_gasto(st.session_state.user, dt, ct, ds, vl)
            st.success("Lançado!")

elif escolha == "👥 Gerenciar Usuários":
    st.header("Painel Administrativo")
    with st.expander("Cadastrar Novo Usuário"):
        new_u = st.text_input("Login")
        new_p = st.text_input("Senha Provisória", type="password")
        new_r = st.radio("Cargo", ["user", "admin"])
        if st.button("Criar Conta"):
            if banco.adicionar_usuario(new_u, new_p, new_r):
                st.success("Usuário criado!")
            else:
                st.error("Usuário já existe!")

else: # Dashboard
    st.header("Visualização de Dados")
    df = banco.buscar_gastos(st.session_state.user, st.session_state.role)
    if not df.empty:
        st.metric("Gasto Total", f"R$ {df['valor'].sum():.2f}")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum dado cadastrado.")