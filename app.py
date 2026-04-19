import streamlit as st
import plotly.express as px
from datetime import date
import banco

st.set_page_config(page_title="Financeiro PRO", layout="wide")

banco.criar_tabelas()

# ================= CONTROLE =================
if "logado" not in st.session_state:
    st.session_state.logado = False

if "pagina" not in st.session_state:
    st.session_state.pagina = "dashboard"

if "menu" not in st.session_state:
    st.session_state.menu = True

# ================= LOGIN =================
if not st.session_state.logado:
    st.title("🔐 Login")

    u = st.text_input("Usuário", key="login_user")
    s = st.text_input("Senha", type="password", key="login_pass")

    if st.button("Entrar", key="btn_login"):
        nivel = banco.validar_login(u, s)
        if nivel:
            st.session_state.logado = True
            st.session_state.user = u
            st.session_state.nivel = nivel
            st.rerun()
        else:
            st.error("Login inválido")

    st.markdown("---")
    st.subheader("🔑 Recuperar senha")

    u2 = st.text_input("Usuário", key="reset_user")
    s2 = st.text_input("Nova senha", type="password", key="reset_pass")

    if st.button("Redefinir senha", key="btn_reset"):
        if u2 and s2:
            banco.redefinir_senha(u2, s2)
            st.success("Senha redefinida")
        else:
            st.warning("Preencha os campos")

# ================= SISTEMA =================
else:
    user = st.session_state.user

    # BOTÃO MENU
    if st.sidebar.button("☰ Menu", key="toggle_menu"):
        st.session_state.menu = not st.session_state.menu

    if st.session_state.menu:

        salario = banco.buscar_salario(user)
        meta = banco.buscar_meta(user)

        # ===== SALÁRIO =====
        with st.sidebar.expander("💰 Salário"):
            novo_salario = st.number_input(
                "Seu salário",
                value=float(salario),
                key="salario_input"
            )
            if st.button("Salvar Salário", key="btn_salvar_salario"):
                banco.atualizar_salario(user, novo_salario)
                st.rerun()

        # ===== META =====
        with st.sidebar.expander("🎯 Meta"):
            nova_meta = st.number_input(
                "Meta",
                value=float(meta),
                key="meta_input"
            )
            if st.button("Salvar Meta", key="btn_salvar_meta"):
                banco.atualizar_meta(user, nova_meta)
                st.rerun()

        # ===== DASHBOARD =====
        with st.sidebar.expander("📊 Dashboard"):
            if st.button("Abrir Dashboard", key="btn_dashboard"):
                st.session_state.pagina = "dashboard"
                st.rerun()

        # ===== GASTO =====
        with st.sidebar.expander("💸 Gasto"):
            if st.button("Novo Gasto", key="btn_gasto"):
                st.session_state.pagina = "gasto"
                st.rerun()

        # ===== CONFIG =====
        with st.sidebar.expander("⚙️ Configurações"):
            if st.button("Abrir Configurações", key="btn_config"):
                st.session_state.pagina = "config"
                st.rerun()

        # ===== ADMIN =====
        if st.session_state.nivel == "admin":
            with st.sidebar.expander("👤 Admin"):
                if st.button("Abrir Admin", key="btn_admin"):
                    st.session_state.pagina = "admin"
                    st.rerun()

        # SAIR
        if st.sidebar.button("Sair", key="btn_sair"):
            st.session_state.logado = False
            st.rerun()

    # ================= DADOS =================
    df = banco.buscar_gastos(user)
    pagina = st.session_state.pagina

    # ================= DASHBOARD =================
    if pagina == "dashboard":
        st.title("📊 Dashboard")

        if not df.empty:
            df['data'] = df['data'].astype('datetime64[ns]')
            df['mes'] = df['data'].dt.to_period('M').astype(str)

            total = df['valor'].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("Salário", f"R$ {salario:.2f}")
            c2.metric("Gastos", f"R$ {total:.2f}")
            c3.metric("Saldo", f"R$ {salario-total:.2f}")

            st.plotly_chart(px.pie(df, values='valor', names='categoria'))

            df_mes = df.groupby('mes')['valor'].sum().reset_index()
            st.plotly_chart(px.bar(df_mes, x='mes', y='valor'))

        else:
            st.info("Sem dados")

    # ================= GASTO =================
    elif pagina == "gasto":
        st.title("💸 Novo Gasto")

        with st.form("form_gasto"):
            d = st.date_input("Data", date.today(), key="data_gasto")
            cat = st.selectbox(
                "Categoria",
                ["Alimentação","Transporte","Moradia","Lazer"],
                key="cat_gasto"
            )
            desc = st.text_input("Descrição", key="desc_gasto")
            val = st.number_input("Valor", min_value=0.0, key="valor_gasto")
            status = st.selectbox("Status", ["Pago","Pendente"], key="status_gasto")

            if st.form_submit_button("Salvar", use_container_width=True):
                banco.salvar_gasto(user, d, cat, desc, val, status)
                st.success("Gasto salvo")
                st.rerun()

    # ================= CONFIG =================
    elif pagina == "config":
        st.title("⚙️ Configurações")

        if not df.empty:
            for _, r in df.iterrows():
                c1, c2 = st.columns([6,1])

                c1.write(
                    f"{r['data']} | {r['descricao']} | R$ {r['valor']:.2f}"
                )

                if c2.button("🗑️", key=f"del_{r['id']}"):
                    banco.deletar_gasto(r['id'])
                    st.rerun()
        else:
            st.info("Sem dados")

    # ================= ADMIN =================
    elif pagina == "admin":
        st.title("👥 Administração")

        df_users = banco.listar_usuarios()

        st.subheader("Usuários")
        st.dataframe(df_users)

        st.subheader("Criar usuário")

        with st.form("form_user"):
            nu = st.text_input("Usuário", key="novo_user")
            ns = st.text_input("Senha", type="password", key="novo_pass")
            nn = st.selectbox("Perfil", ["user","admin"], key="novo_nivel")

            if st.form_submit_button("Criar"):
                banco.adicionar_usuario(nu, ns, nn)
                st.success("Usuário criado")
                st.rerun()

        st.subheader("Gerenciar")

        for _, r in df_users.iterrows():
            with st.expander(r['usuario']):

                nova_senha = st.text_input(
                    "Nova senha",
                    type="password",
                    key=f"senha_{r['usuario']}"
                )

                if st.button("Alterar senha", key=f"btn_senha_{r['usuario']}"):
                    if nova_senha:
                        banco.alterar_senha(r['usuario'], nova_senha)
                        st.success("Senha atualizada")

                novo_nivel = st.selectbox(
                    "Perfil",
                    ["user","admin"],
                    index=0 if r['nivel']=="user" else 1,
                    key=f"nivel_{r['usuario']}"
                )

                if st.button("Salvar perfil", key=f"btn_nivel_{r['usuario']}"):
                    banco.alterar_nivel(r['usuario'], novo_nivel)
                    st.success("Perfil atualizado")
                    st.rerun()
