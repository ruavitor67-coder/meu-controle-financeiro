import streamlit as st
import plotly.express as px
from datetime import date

import banco
import utils

st.set_page_config(page_title="Financeiro PRO", layout="wide")

banco.criar_tabelas()

if "logado" not in st.session_state:
    st.session_state.logado = False

# LOGIN
if not st.session_state.logado:
    st.title("🔐 Login")

    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        nivel = banco.validar_login(u, s)
        if nivel:
            st.session_state.logado = True
            st.session_state.user = u
            st.session_state.nivel = nivel
            st.rerun()
        else:
            st.error("Login inválido")

# SISTEMA
else:
    st.sidebar.title(f"👤 {st.session_state.user}")

    salario = banco.buscar_salario(st.session_state.user)
    meta = banco.buscar_meta(st.session_state.user)

    st.sidebar.metric("Salário", f"R$ {salario:.2f}")

    with st.sidebar.expander("Meta"):
        nova_meta = st.number_input("Meta", value=float(meta))
        if st.button("Salvar Meta"):
            banco.atualizar_meta(st.session_state.user, nova_meta)
            st.rerun()

    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    df = banco.buscar_gastos(st.session_state.user)
    df = utils.preparar_dados(df)

    st.title("📊 Dashboard")

    if not df.empty:
        total = df['valor'].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Salário", f"R$ {salario:.2f}")
        c2.metric("Gastos", f"R$ {total:.2f}")
        c3.metric("Saldo", f"R$ {salario-total:.2f}")

        fig = px.pie(df, values='valor', names='categoria')
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Sem dados")

    st.subheader("Novo Gasto")

    d = st.date_input("Data", date.today())
    cat = st.selectbox("Categoria", ["Alimentação","Transporte","Moradia","Lazer"])
    desc = st.text_input("Descrição")
    val = st.number_input("Valor", min_value=0.0)
    status = st.selectbox("Status", ["Pago","Pendente"])

    if st.button("Salvar"):
        banco.salvar_gasto(st.session_state.user, d, cat, desc, val, status)
        st.success("Salvo")
        st.rerun()
