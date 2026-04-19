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
        nova_meta = st.number_input("Meta mensal", value=float(meta))
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

    # ================= DASHBOARD =================
    if escolha == "Dashboard":
        st.title("📊 Dashboard")

        if not df.empty:
            total = df['valor'].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("Salário", f"R$ {salario:.2f}")
            c2.metric("Gastos", f"R$ {total:.2f}")
            c3.metric("Saldo", f"R$ {salario-total:.2f}")

            # META
            if meta > 0:
                progresso = total / meta
                st.subheader("Progresso da Meta")
                st.progress(min(progresso, 1.0))

            # FILTRO
            col1, col2 = st.columns(2)
            inicio = col1.date_input("Data inicial", date.today())
            fim = col2.date_input("Data final", date.today())

            df_filtrado = df[
                (df['data'] >= str(inicio)) &
                (df['data'] <= str(fim))
            ]

            # GRÁFICO PIZZA
            fig = px.pie(df_filtrado, values='valor', names='categoria')
            st.plotly_chart(fig, use_container_width=True)

            # LISTA DE GASTOS
            st.subheader("📋 Lançamentos")

            for _, row in df.iterrows():
                col1, col2, col3 = st.columns([5,1,1])

                col1.info(
                    f"{row['data']} | {row['categoria']} | "
                    f"{row['descricao']} | R$ {row['valor']:.2f}"
                )

                if row['status'] == "Pago":
                    col2.success("Pago")
                else:
                    col2.warning("Pendente")

                if col3.button("🗑️", key=row['id']):
                    banco.deletar_gasto(row['id'])
                    st.rerun()

            # DOWNLOAD CSV
            csv = df.to_csv(index=False).encode()
            st.download_button("📥 Baixar CSV", csv, "gastos.csv")

        else:
            st.info("Sem dados ainda — cadastre um gasto 👇")

    # ================= NOVO GASTO =================
    elif escolha == "Novo Gasto":
        st.title("💸 Novo Gasto")

        with st.form("form"):
            d = st.date_input("Data", date.today())
            cat = st.selectbox(
                "Categoria",
                ["Alimentação","Transporte","Moradia","Lazer"]
            )
            desc = st.text_input("Descrição")
            val = st.number_input("Valor", min_value=0.0)
            status = st.selectbox("Status", ["Pago","Pendente"])

            if st.form_submit_button("Salvar"):
                banco.salvar_gasto(
                    st.session_state.user, d, cat, desc, val, status
                )
                st.success("Salvo")
                st.rerun()

    # ================= ADMIN =================
    elif escolha == "Admin":
        st.title("👥 Admin")

        with st.form("user"):
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            n = st.selectbox("Perfil", ["user","admin"])

            if st.form_submit_button("Criar"):
                if banco.adicionar_usuario(u, s, n):
                    st.success("Criado")
                else:
                    st.error("Erro")

        st.dataframe(banco.listar_usuarios())
