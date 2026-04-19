import streamlit as st
import plotly.express as px
from datetime import date
import banco

st.set_page_config(page_title="Financeiro PRO", layout="wide")

banco.criar_tabelas()

# ================= ESTADO =================
if "logado" not in st.session_state:
    st.session_state.logado = False

if "pagina" not in st.session_state:
    st.session_state.pagina = "dashboard"

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

    # ================= RECUPERAÇÃO =================
    st.markdown("---")
    st.subheader("🔑 Recuperar senha")

    user_reset = st.text_input("Usuário para recuperação", key="reset_user")

    if st.button("Enviar código", key="btn_codigo"):
        email = banco.buscar_email(user_reset)

        if email:
            codigo = banco.gerar_codigo()
            banco.salvar_codigo(user_reset, codigo)
            banco.enviar_email(email, codigo)

            st.session_state.reset_user_ok = user_reset
            st.success("Código enviado para o e-mail")
        else:
            st.error("Usuário não encontrado")

    if "reset_user_ok" in st.session_state:

        codigo_digitado = st.text_input("Código recebido", key="codigo_input")

        if st.button("Validar código", key="btn_validar"):
            if banco.validar_codigo(st.session_state.reset_user_ok, codigo_digitado):
                st.session_state.codigo_valido = True
                st.success("Código validado ✅")
            else:
                st.error("Código inválido ou expirado")

    if st.session_state.get("codigo_valido"):

        nova_senha = st.text_input("Nova senha", type="password", key="nova_senha")

        if st.button("Confirmar troca", key="btn_confirmar"):
            banco.redefinir_senha(st.session_state.reset_user_ok, nova_senha)

            del st.session_state["codigo_valido"]
            del st.session_state["reset_user_ok"]

            st.success("Senha alterada com sucesso")

# ================= SISTEMA =================
else:

    user = st.session_state.user

    # ================= SIDEBAR =================
    with st.sidebar:

        st.title(f"👤 {user}")

        # SALÁRIO
        salario = banco.buscar_salario(user)
        with st.expander("💰 Salário"):
            novo_salario = st.number_input("Valor", value=float(salario), key="salario")
            if st.button("Salvar Salário", key="btn_salario"):
                banco.atualizar_salario(user, novo_salario)
                st.rerun()

        # META
        meta = banco.buscar_meta(user)
        with st.expander("🎯 Meta"):
            nova_meta = st.number_input("Valor", value=float(meta), key="meta")
            if st.button("Salvar Meta", key="btn_meta"):
                banco.atualizar_meta(user, nova_meta)
                st.rerun()

        st.markdown("---")

        if st.button("📊 Dashboard", key="nav_dash"):
            st.session_state.pagina = "dashboard"
            st.rerun()

        if st.button("💸 Gasto", key="nav_gasto"):
            st.session_state.pagina = "gasto"
            st.rerun()

        if st.button("⚙️ Configurações", key="nav_config"):
            st.session_state.pagina = "config"
            st.rerun()

        if st.session_state.nivel == "admin":
            if st.button("👤 Admin", key="nav_admin"):
                st.session_state.pagina = "admin"
                st.rerun()

        st.markdown("---")

        if st.button("Sair", key="btn_sair"):
            st.session_state.logado = False
            st.rerun()

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
            c3.metric("Saldo", f"R$ {salario - total:.2f}")

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
            cat = st.selectbox("Categoria",
                               ["Alimentação","Transporte","Moradia","Lazer"],
                               key="cat_gasto")
            desc = st.text_input("Descrição", key="desc_gasto")
            val = st.number_input("Valor", min_value=0.0, key="valor_gasto")
            status = st.selectbox("Status", ["Pago","Pendente"], key="status_gasto")

            if st.form_submit_button("Salvar"):
                banco.salvar_gasto(user, d, cat, desc, val, status)
                st.success("Gasto salvo")
                st.rerun()

    # ================= CONFIG =================
    elif pagina == "config":

        st.title("⚙️ Configurações")

        if not df.empty:
            for _, r in df.iterrows():
                c1, c2 = st.columns([6,1])
                c1.write(f"{r['data']} | {r['descricao']} | R$ {r['valor']:.2f}")

                if c2.button("🗑️", key=f"del_{r['id']}"):
                    banco.deletar_gasto(r['id'])
                    st.rerun()
        else:
            st.info("Sem dados")

    # ================= ADMIN =================
    elif pagina == "admin":

        st.title("👥 Administração")

        df_users = banco.listar_usuarios()
        st.dataframe(df_users)

        st.subheader("Criar usuário")

        with st.form("form_user"):
            nu = st.text_input("Usuário", key="novo_user")
            email = st.text_input("Email", key="novo_email")
            ns = st.text_input("Senha", type="password", key="novo_pass")
            nn = st.selectbox("Perfil", ["user","admin"], key="novo_nivel")

            if st.form_submit_button("Criar"):
                banco.adicionar_usuario(nu, email, ns, nn)
                st.success("Usuário criado")
                st.rerun()

        st.subheader("Gerenciar usuários")

        for _, r in df_users.iterrows():
            with st.expander(r['usuario']):

                nova_senha = st.text_input("Nova senha", type="password", key=f"senha_{r['usuario']}")

                if st.button("Alterar senha", key=f"btn_senha_{r['usuario']}"):
                    if nova_senha:
                        banco.redefinir_senha(r['usuario'], nova_senha)
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

                st.markdown("---")

                # EXCLUIR USUÁRIO
                if r['usuario'] != st.session_state.user and r['usuario'] != "admin":

                    if st.button("🗑️ Excluir usuário", key=f"del_{r['usuario']}"):
                        banco.deletar_usuario(r['usuario'])
                        st.success("Usuário excluído")
                        st.rerun()
                else:
                    st.warning("Usuário protegido")
