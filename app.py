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
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 Lançamentos")

            for _, row in df.iterrows():
                col1, col2, col3 = st.columns([5,1,1])

                col1.info(
                    f"{row['data']} | {row['categoria']} | {row['descricao']} | R$ {row['valor']:.2f}"
                )

                col2.write(row['status'])

                if col3.button("🗑️", key=row['id']):
                    banco.deletar_gasto(row['id'])
                    st.rerun()
        else:
            st.info("Sem dados")

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
                st.success("Salvo")
                st.rerun()

    # ADMIN
    elif escolha == "Admin":
        st.title("👥 Administração")

        df_users = banco.listar_usuarios()

        for _, row in df_users.iterrows():
            with st.expander(f"👤 {row['usuario']}"):

                col1, col2 = st.columns(2)

                novo_salario = col1.number_input(
                    "Salário",
                    value=float(row['salario']),
                    key=f"sal_{row['usuario']}"
                )

                if col1.button("Salvar Salário", key=f"btn_sal_{row['usuario']}"):
                    banco.atualizar_salario_admin(row['usuario'], novo_salario)
                    st.rerun()

                novo_nivel = col2.selectbox(
                    "Perfil",
                    ["user","admin"],
                    index=0 if row['nivel']=="user" else 1,
                    key=f"nivel_{row['usuario']}"
                )

                if col2.button("Salvar Perfil", key=f"btn_nivel_{row['usuario']}"):
                    banco.alterar_nivel(row['usuario'], novo_nivel)
                    st.rerun()

                nova_senha = st.text_input(
                    "Nova senha",
                    type="password",
                    key=f"senha_{row['usuario']}"
                )

                if st.button("Alterar Senha", key=f"btn_senha_{row['usuario']}"):
                    if nova_senha:
                        banco.alterar_senha(row['usuario'], nova_senha)
                        st.success("Senha alterada")
