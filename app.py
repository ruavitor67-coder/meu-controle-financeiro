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

    # SALÁRIO NA SIDEBAR
    with st.sidebar.expander("💰 Salário"):
        novo_salario = st.number_input("Seu salário", value=float(salario))
        if st.button("Salvar Salário"):
            banco.atualizar_salario(st.session_state.user, novo_salario)
            st.rerun()

    # META NA SIDEBAR
    with st.sidebar.expander("🎯 Meta"):
        nova_meta = st.number_input("Meta", value=float(meta))
        if st.button("Salvar Meta"):
            banco.atualizar_meta(st.session_state.user, nova_meta)
            st.rerun()

    menu = ["Dashboard", "Novo Gasto"]
    if st.session_state.nivel == "admin":
        menu.append("Admin")

    escolha = st.sidebar.selectbox("Menu", menu)

    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    df = banco.buscar_gastos(st.session_state.user)
    df = utils.preparar_dados(df)

    # DASHBOARD
    if escolha == "Dashboard":
        st.title("📊 Dashboard")

        if not df.empty:
            total = df['valor'].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("Salário", f"R$ {salario:.2f}")
            c2.metric("Gastos", f"R$ {total:.2f}")
            c3.metric("Saldo", f"R$ {salario-total:.2f}")

            fig = px.pie(df, values='valor', names='categoria')
            st.plotly_chart(fig)

    # NOVO GASTO
    elif escolha == "Novo Gasto":
        st.title("💸 Novo Gasto")

        with st.form("form"):
            d = st.date_input("Data", date.today())
            cat = st.selectbox("Categoria", ["Alimentação","Transporte","Moradia","Lazer"])
            desc = st.text_input("Descrição")
            val = st.number_input("Valor", min_value=0.0)
            status = st.selectbox("Status", ["Pago","Pendente"])

            if st.form_submit_button("Salvar"):
                banco.salvar_gasto(st.session_state.user, d, cat, desc, val, status)
                st.rerun()

    # ADMIN
    elif escolha == "Admin":
        st.title("👥 Administração")

        abas = st.tabs(["👤 Usuários", "🔐 Segurança"])
        df_users = banco.listar_usuarios()

        with abas[0]:
            with st.form("novo_user"):
                u = st.text_input("Usuário")
                s = st.text_input("Senha", type="password")
                n = st.selectbox("Perfil", ["user","admin"])

                if st.form_submit_button("Criar"):
                    banco.adicionar_usuario(u, s, n)
                    st.rerun()

            st.dataframe(df_users)

        with abas[1]:
            for _, row in df_users.iterrows():
                with st.expander(row['usuario']):
                    nova_senha = st.text_input("Nova senha", type="password", key=row['usuario'])

                    if st.button("Alterar Senha", key="s"+row['usuario']):
                        banco.alterar_senha(row['usuario'], nova_senha)

                    novo_nivel = st.selectbox(
                        "Perfil",
                        ["user","admin"],
                        index=0 if row['nivel']=="user" else 1,
                        key="n"+row['usuario']
                    )

                    if st.button("Salvar Perfil", key="p"+row['usuario']):
                        banco.alterar_nivel(row['usuario'], novo_nivel)
                        st.rerun()
