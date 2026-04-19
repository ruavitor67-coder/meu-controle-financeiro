import streamlit as st
import plotly.express as px
from datetime import date

import banco
import utils

st.set_page_config(page_title="Financeiro PRO", layout="wide")

banco.criar_tabelas()

# ================= CONTROLE =================
if "logado" not in st.session_state:
    st.session_state.logado = False

if "pagina" not in st.session_state:
    st.session_state.pagina = "dashboard"

# ================= LOGIN =================
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

# ================= SISTEMA =================
else:
    user = st.session_state.user

    st.sidebar.title(f"👤 {user}")

    salario = banco.buscar_salario(user)
    meta = banco.buscar_meta(user)

    # ===== SALÁRIO =====
    with st.sidebar.expander("💰 Salário"):
        novo_salario = st.number_input("Seu salário", value=float(salario))
        if st.button("Salvar Salário"):
            banco.atualizar_salario(user, novo_salario)
            st.rerun()

    # ===== META =====
    with st.sidebar.expander("🎯 Meta"):
        nova_meta = st.number_input("Meta", value=float(meta))
        if st.button("Salvar Meta"):
            banco.atualizar_meta(user, nova_meta)
            st.rerun()

    # ===== DASHBOARD =====
    with st.sidebar.expander("📊 Dashboard"):
        if st.button("Abrir Dashboard"):
            st.session_state.pagina = "dashboard"
            st.rerun()

    # ===== GASTO =====
    with st.sidebar.expander("💸 Gasto"):
        if st.button("Novo Gasto"):
            st.session_state.pagina = "gasto"
            st.rerun()

    # ===== CONFIGURAÇÕES =====
    with st.sidebar.expander("⚙️ Configurações"):
        if st.button("Abrir Configurações"):
            st.session_state.pagina = "config"
            st.rerun()

    # ===== ADMIN =====
    if st.session_state.nivel == "admin":
        with st.sidebar.expander("👤 Admin"):
            if st.button("Abrir Admin"):
                st.session_state.pagina = "admin"
                st.rerun()

    # SAIR
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # ================= DADOS =================
    df = banco.buscar_gastos(user)
    df = utils.preparar_dados(df)

    pagina = st.session_state.pagina

    # ================= DASHBOARD =================
    if pagina == "dashboard":
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

    # ================= GASTO =================
    elif pagina == "gasto":
        st.title("💸 Novo Gasto")

        with st.form("form_gasto"):
            d = st.date_input("Data", date.today())
            cat = st.selectbox("Categoria", ["Alimentação","Transporte","Moradia","Lazer"])
            desc = st.text_input("Descrição")
            val = st.number_input("Valor", min_value=0.0)
            status = st.selectbox("Status", ["Pago","Pendente"])

            if st.form_submit_button("Salvar"):
                banco.salvar_gasto(user, d, cat, desc, val, status)
                st.success("Salvo")
                st.rerun()

    # ================= CONFIGURAÇÕES =================
    elif pagina == "config":
        st.title("⚙️ Configurações")

        if not df.empty:
            for _, row in df.iterrows():
                col1, col2 = st.columns([6,1])

                col1.write(
                    f"{row['data']} | {row['categoria']} | {row['descricao']} | R$ {row['valor']:.2f}"
                )

                if col2.button("🗑️", key=row['id']):
                    banco.deletar_gasto(row['id'])
                    st.rerun()
        else:
            st.info("Sem dados")

    # ================= ADMIN =================
    elif pagina == "admin":
        st.title("👥 Administração")

        abas = st.tabs(["Usuários", "Segurança"])
        df_users = banco.listar_usuarios()

        # USUÁRIOS
        with abas[0]:
            with st.form("novo_user"):
                u = st.text_input("Usuário")
                s = st.text_input("Senha", type="password")
                n = st.selectbox("Perfil", ["user","admin"])

                if st.form_submit_button("Criar"):
                    banco.adicionar_usuario(u, s, n)
                    st.rerun()

            st.dataframe(df_users)

        # SEGURANÇA
        with abas[1]:
            for _, row in df_users.iterrows():
                with st.expander(row['usuario']):
                    nova_senha = st.text_input("Nova senha", type="password", key=row['usuario'])

                    if st.button("Alterar Senha", key="s"+row['usuario']):
                        banco.alterar_senha(row['usuario'], nova_senha)
                        st.success("Senha alterada")

                    novo_nivel = st.selectbox(
                        "Perfil",
                        ["user","admin"],
                        index=0 if row['nivel']=="user" else 1,
                        key="n"+row['usuario']
                    )

                    if st.button("Salvar Perfil", key="p"+row['usuario']):
                        banco.alterar_nivel(row['usuario'], novo_nivel)
                        st.success("Perfil atualizado")
                        st.rerun()
