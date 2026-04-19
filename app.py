import streamlit as st
import plotly.express as px
from datetime import date

import banco
import utils

st.set_page_config(page_title="Financeiro PRO", layout="wide")

banco.criar_tabelas()

if "logado" not in st.session_state:
    st.session_state.logado = False

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
    st.sidebar.title(f"👤 {st.session_state.user}")

    salario = banco.buscar_salario(st.session_state.user)
    meta = banco.buscar_meta(st.session_state.user)

    # ===== SALÁRIO =====
    with st.sidebar.expander("💰 Salário"):
        novo_salario = st.number_input(
            "Seu salário",
            value=float(salario),
            key="salario_usuario"
        )
        if st.button("Salvar Salário"):
            banco.atualizar_salario(st.session_state.user, novo_salario)
            st.success("Salário atualizado")
            st.rerun()

    # ===== META =====
    with st.sidebar.expander("🎯 Meta"):
        nova_meta = st.number_input(
            "Meta",
            value=float(meta),
            key="meta_usuario"
        )
        if st.button("Salvar Meta"):
            banco.atualizar_meta(st.session_state.user, nova_meta)
            st.success("Meta atualizada")
            st.rerun()

    st.sidebar.markdown("---")

    # ===== MENU =====
    menu = ["Configurações"]
    if st.session_state.nivel == "admin":
        menu.insert(0, "Admin")

    escolha = st.sidebar.radio("Menu", menu)

    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # ================= CONFIGURAÇÕES =================
    if escolha == "Configurações":
        st.title("⚙️ Configurações")

        df = banco.buscar_gastos(st.session_state.user)
        df = utils.preparar_dados(df)

        # DASHBOARD
        st.subheader("📊 Resumo")

        if not df.empty:
            total = df['valor'].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("Salário", f"R$ {salario:.2f}")
            c2.metric("Gastos", f"R$ {total:.2f}")
            c3.metric("Saldo", f"R$ {salario-total:.2f}")

            fig = px.pie(df, values='valor', names='categoria')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados ainda")

        # LISTA DE GASTOS
        st.subheader("📋 Seus Gastos")

        if not df.empty:
            for _, row in df.iterrows():
                col1, col2 = st.columns([6,1])

                col1.write(
                    f"{row['data']} | {row['categoria']} | {row['descricao']} | R$ {row['valor']:.2f}"
                )

                if col2.button("🗑️", key=row['id']):
                    banco.deletar_gasto(row['id'])
                    st.rerun()

        # NOVO GASTO
        st.markdown("---")
        st.subheader("💸 Novo Gasto")

        with st.form("form_gasto"):
            d = st.date_input("Data", date.today())
            cat = st.selectbox("Categoria", ["Alimentação","Transporte","Moradia","Lazer"])
            desc = st.text_input("Descrição")
            val = st.number_input("Valor", min_value=0.0)
            status = st.selectbox("Status", ["Pago","Pendente"])

            if st.form_submit_button("Salvar"):
                banco.salvar_gasto(
                    st.session_state.user, d, cat, desc, val, status
                )
                st.success("Gasto salvo")
                st.rerun()

    # ================= ADMIN =================
    elif escolha == "Admin":
        st.title("👥 Administração")

        abas = st.tabs(["👤 Usuários", "🔐 Segurança"])
        df_users = banco.listar_usuarios()

        # USUÁRIOS
        with abas[0]:
            st.subheader("Criar usuário")

            with st.form("novo_user"):
                u = st.text_input("Usuário")
                s = st.text_input("Senha", type="password")
                n = st.selectbox("Perfil", ["user","admin"])

                if st.form_submit_button("Criar"):
                    if banco.adicionar_usuario(u, s, n):
                        st.success("Usuário criado")
                        st.rerun()
                    else:
                        st.error("Usuário já existe")

            st.divider()
            st.subheader("Lista")
            st.dataframe(df_users)

        # SEGURANÇA
        with abas[1]:
            st.subheader("Gerenciar usuários")

            for _, row in df_users.iterrows():
                with st.expander(row['usuario']):

                    nova_senha = st.text_input(
                        "Nova senha",
                        type="password",
                        key="senha_"+row['usuario']
                    )

                    if st.button("Alterar Senha", key="btn_senha_"+row['usuario']):
                        if nova_senha:
                            banco.alterar_senha(row['usuario'], nova_senha)
                            st.success("Senha alterada")

                    novo_nivel = st.selectbox(
                        "Perfil",
                        ["user","admin"],
                        index=0 if row['nivel']=="user" else 1,
                        key="nivel_"+row['usuario']
                    )

                    if st.button("Salvar Perfil", key="btn_nivel_"+row['usuario']):
                        banco.alterar_nivel(row['usuario'], novo_nivel)
                        st.success("Perfil atualizado")
                        st.rerun()
