import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

# Configuração da Página
st.set_page_config(page_title="Meu Controle Financeiro", page_icon="💰", layout="wide")

# Iniciar Banco
banco.criar_tabelas()

# Controle de Login
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = ""
    st.session_state.role = ""

if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        role = banco.validar_login(u, p)
        if role:
            st.session_state.logado = True
            st.session_state.user = u
            st.session_state.role = role
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")
    st.stop()

# --- MENU LATERAL ---
st.sidebar.title(f"Olá, {st.session_state.user}")
opcoes = ["📊 Resumo", "💸 Novo Gasto"]
if st.session_state.role == 'admin':
    opcoes.append("👥 Usuários")

escolha = st.sidebar.selectbox("Ir para:", opcoes)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---
if escolha == "💸 Novo Gasto":
    st.header("Registrar Gasto")
    with st.form("form_gasto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        data = col1.date_input("Data")
        # Personalize suas categorias aqui:
        cat = col2.selectbox("Categoria", ["Mercado", "Lazer", "Contas Fixas", "Saúde", "Outros"])
        desc = st.text_input("O que você comprou?")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        
        if st.form_submit_button("Salvar"):
            if desc and valor > 0:
                banco.salvar_gasto(st.session_state.user, data, cat, desc, valor)
                st.success("Gasto salvo com sucesso!")
            else:
                st.warning("Preencha a descrição e o valor.")

elif escolha == "👥 Usuários":
    st.header("Gerenciar Usuários")
    new_u = st.text_input("Nome do novo usuário")
    new_p = st.text_input("Senha inicial", type="password")
    if st.button("Criar Usuário"):
        if banco.adicionar_usuario(new_u, new_p, 'user'):
            st.success("Usuário criado!")
        else:
            st.error("Erro ao criar (usuário já existe).")

else: # TELA RESUMO (DASHBOARD)
    st.header("📊 Seu Resumo Financeiro")
    df = banco.buscar_gastos(st.session_state.user, st.session_state.role)
    
    if not df.empty:
        # Métricas
        c1, c2 = st.columns(2)
        c1.metric("Total Gasto", f"R$ {df['valor'].sum():.2f}")
        c2.metric("Lançamentos", len(df))
        
        # Gráfico de Pizza
        st.subheader("Gastos por Categoria")
        df_pizza = df.groupby("categoria")["valor"].sum().reset_index()
        fig = px.pie(df_pizza, values='valor', names='categoria', hole=0.3)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela
        with st.expander("Ver lista detalhada"):
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Dados", data=csv, file_name="meus_gastos.csv")
    else:
        st.info("Você ainda não tem gastos registrados. Vá em 'Novo Gasto'!")
