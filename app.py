import streamlit as st
import plotly.express as px
from datetime import date
import banco
import time

st.set_page_config(page_title="Financeiro PRO", layout="wide")

banco.criar_tabelas()

# ================= ESTADO =================
if "logado" not in st.session_state:
    st.session_state.logado = False

if "pagina" not in st.session_state:
    st.session_state.pagina = "dashboard"

if "tentativas" not in st.session_state:
    st.session_state.tentativas = 0

if "bloqueado_ate" not in st.session_state:
    st.session_state.bloqueado_ate = None

# ================= LOGIN =================
if not st.session_state.logado:

    st.title("🔐 Login")

    # BLOQUEIO
    if st.session_state.bloqueado_ate:
        if time.time() < st.session_state.bloqueado_ate:
            st.error("🚫 Muitas tentativas. Aguarde 30 segundos.")
            st.stop()
        else:
            st.session_state.tentativas = 0
            st.session_state.bloqueado_ate = None

    u = st.text_input("Usuário", key="login_user")
    s = st.text_input("Senha", type="password", key="login_pass")

    if st.button("Entrar", key="btn_login"):
        nivel = banco.validar_login(u, s)

        if nivel:
            st.session_state.logado = True
            st.session_state.user = u
            st.session_state.nivel = nivel
            st.session_state.tentativas = 0
            st.rerun()
        else:
            st.session_state.tentativas += 1
            st.error(f"Login inválido ({st.session_state.tentativas}/3)")

            if st.session_state.tentativas >= 3:
                st.session_state.bloqueado_ate = time.time() + 30
                st.error("🚫 Bloqueado por 30 segundos")
                st.rerun()

    # ================= RECUPERAÇÃO =================
    st.markdown("---")
    st.subheader("🔑 Recuperar senha")

    user_reset = st.text_input("Usuário", key="reset_user")

    if st.button("Enviar código", key="btn_codigo"):
        email = banco.buscar_email(user_reset)

        if email:
            codigo = banco.gerar_codigo()
            banco.salvar_codigo(user_reset, codigo)
            banco.enviar_email(email, codigo)

            st.session_state.reset_user_ok = user_reset
            st.success("Código enviado")
        else:
            st.error("Usuário não encontrado")

    if "reset_user_ok" in st.session_state:

        codigo = st.text_input("Código", key="codigo")

        if st.button("Validar", key="btn_validar"):
            if banco.validar_codigo(st.session_state.reset_user_ok, codigo):
                st.session_state.codigo_valido = True
                st.success("Código válido")
            else:
                st.error("Código inválido")

    if st.session_state.get("codigo_valido"):

        nova = st.text_input("Nova senha", type="password", key="nova")

        if st.button("Confirmar", key="btn_confirmar"):
            banco.redefinir_senha(st.session_state.reset_user_ok, nova)

            del st.session_state["codigo_valido"]
            del st.session_state["reset_user_ok"]

            st.success("Senha alterada")

# ================= SISTEMA =================
else:

    user = st.session_state.user

    with st.sidebar:

        st.title(user)

        salario = banco.buscar_salario(user)
        meta = banco.buscar_meta(user)

        salario_input = st.number_input("Salário", value=float(salario))
        if st.button("Salvar salário"):
            banco.atualizar_salario(user, salario_input)
            st.rerun()

        meta_input = st.number_input("Meta", value=float(meta))
        if st.button("Salvar meta"):
            banco.atualizar_meta(user, meta_input)
            st.rerun()

        if st.button("Dashboard"):
            st.session_state.pagina = "dashboard"

        if st.button("Gasto"):
            st.session_state.pagina = "gasto"

        if st.button("Config"):
            st.session_state.pagina = "config"

        if st.session_state.nivel == "admin":
            if st.button("Admin"):
                st.session_state.pagina = "admin"

        if st.button("Sair"):
            st.session_state.logado = False
            st.rerun()

    df = banco.buscar_gastos(user)

    if st.session_state.pagina == "dashboard":
        st.title("Dashboard")

        if not df.empty:
            total = df["valor"].sum()
            st.metric("Saldo", f"R$ {salario-total:.2f}")
            st.plotly_chart(px.pie(df, values="valor", names="categoria"))

    elif st.session_state.pagina == "gasto":
        st.title("Novo Gasto")

        with st.form("gasto"):
            d = st.date_input("Data", date.today())
            cat = st.text_input("Categoria")
            desc = st.text_input("Descrição")
            val = st.number_input("Valor", min_value=0.0)
            status = st.selectbox("Status", ["Pago","Pendente"])

            if st.form_submit_button("Salvar"):
                banco.salvar_gasto(user, d, cat, desc, val, status)
                st.success("Salvo")
                st.rerun()

    elif st.session_state.pagina == "config":
        st.title("Configurações")

        for _, r in df.iterrows():
            st.write(r["descricao"], r["valor"])
            if st.button("Excluir", key=f"del_{r['id']}"):
                banco.deletar_gasto(r["id"])
                st.rerun()

    elif st.session_state.pagina == "admin":
        st.title("Admin")

        users = banco.listar_usuarios()

        for _, r in users.iterrows():
            st.write(r["usuario"])

            if r["usuario"] != user and r["usuario"] != "admin":

                if st.button("Excluir usuário", key=f"del_user_{r['usuario']}"):
                    st.session_state[f"conf_{r['usuario']}"] = True

                if st.session_state.get(f"conf_{r['usuario']}"):
                    if st.button("Confirmar exclusão", key=f"conf_btn_{r['usuario']}"):
                        banco.deletar_usuario(r["usuario"])
                        st.success("Excluído")
                        st.rerun()
