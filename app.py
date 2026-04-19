import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

# 1. Configuração da Página
st.set_page_config(page_title="Controle Financeiro", page_icon="💰", layout="wide")

# 2. Iniciar Banco de Dados
banco.criar_tabelas()

# 3. Controle de Sessão
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = ""
    st.session_state.role = ""

# --- TELA DE LOGIN ---
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
            st.error("Usuário ou senha incorretos!")
    st.stop()

# --- MENU LATERAL ---
st.sidebar.title(f"👤 {st.session_state.user.upper()}")
menu = ["📊 Dashboard", "💸 Lançar Gastos", "👥 Gerenciar Usuários"]
escolha = st.sidebar.selectbox("Navegação:", menu)

st.sidebar.divider()
if st.sidebar.button("Sair / Logout", use_container_width=True):
    st.session_state.logado = False
    st.rerun()

# --- LÓGICA DAS TELAS ---
if escolha == "💸 Lançar Gastos":
    st.header("💸 Novo Lançamento")
    with st.form("form_gastos", clear_on_submit=True):
        col1, col2 = st.columns(2)
        dt = col1.date_input("Data do Gasto", format="DD/MM/YYYY")
        ct = col2.selectbox("Categoria", ["Alimentação", "Transporte", "Saúde", "Lazer", "Educação", "Fixos", "Outros"])
        ds = st.text_input("Descrição")
        vl = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        
        if st.form_submit_button("Salvar Registro", use_container_width=True):
            if ds and vl > 0:
                banco.salvar_gasto(st.session_state.user, dt, ct, ds, vl)
                st.success("Gasto registrado com sucesso!")
            else:
                st.warning("Preencha a descrição e o valor.")

elif escolha == "👥 Gerenciar Usuários":
    st.header("👥 Cadastro de Usuários")
    with st.expander("➕ Adicionar Novo Usuário"):
        new_u = st.text_input("Nome de Usuário")
        new_p = st.text_input("Senha", type="password")
        new_r = st.radio("Nível", ["user", "admin"], horizontal=True)
        if st.button("Criar Conta"):
            if new_u and new_p:
                if banco.adicionar_usuario(new_u, new_p, new_r):
                    st.success(f"Usuário '{new_u}' criado!")
                else:
                    st.error("Erro: Usuário já existe.")

else: # TELA: DASHBOARD
    st.header("📊 Resumo Financeiro")
    df = banco.buscar_gastos(st.session_state.user, st.session_state.role)
    
    if not df.empty:
        total = df['valor'].sum()
        qtd = len(df)
        
        c1, c2 = st.columns(2)
        c1.metric("Gasto Total", f"R$ {total:.2f}")
        c2.metric("Lançamentos", qtd)
        
        st.divider()
        df_agrupado = df.groupby("categoria")["valor"].sum().reset_index()
        fig = px.pie(df_agrupado, values='valor', names='categoria', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📂 Ver Histórico Detalhado"):
            st.dataframe(df.sort_values(by="data", ascending=False), use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar CSV", data=csv, file_name="gastos.csv", mime="text/csv")
    else:
        st.info("Nenhum dado cadastrado.")
