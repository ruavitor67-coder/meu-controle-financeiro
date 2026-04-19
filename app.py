import streamlit as st
import banco
from datetime import date

st.set_page_config(layout="wide")

# ================= PROTEÇÃO =================
try:
    banco.criar_tabelas()
except Exception as e:
    st.error(f"Erro banco: {e}")
    st.stop()


# ================= LOGIN =================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("Login")

    u = st.text_input("Usuário", key="login_user")
    s = st.text_input("Senha", type="password", key="login_pass")

    if st.button("Entrar"):
        nivel = banco.validar_login(u, s)
        if nivel:
            st.session_state.logado = True
            st.session_state.user = u
            st.session_state.nivel = nivel
            st.rerun()
        else:
            st.error("Login inválido")

    st.stop()


# ================= SIDEBAR =================
st.sidebar.title(st.session_state.user)

menu = st.sidebar.selectbox(
    "Menu",
    ["Dashboard", "Novo Gasto", "Admin"]
)


# ================= DASHBOARD =================
if menu == "Dashboard":
    st.title("Dashboard")

    dados = banco.listar_gastos(st.session_state.user)
    st.write(dados)


# ================= NOVO GASTO =================
elif menu == "Novo Gasto":
    st.title("Novo Gasto")

    data = st.date_input("Data", value=date.today())
    cat = st.selectbox("Categoria", [
        "Alimentação", "Transporte", "Moradia",
        "Lazer", "Saúde", "Educação"
    ])
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor")
    status = st.selectbox("Status", ["Pago", "Pendente"])

    if st.button("Salvar"):
        banco.salvar_gasto(
            st.session_state.user,
            data, cat, desc, valor, status
        )
        st.success("Salvo com sucesso")


# ================= ADMIN =================
elif menu == "Admin":

    if st.session_state.nivel != "admin":
        st.warning("Sem permissão")
        st.stop()

    st.title("Admin")

    tab1, tab2, tab3 = st.tabs(["Usuários", "Salário", "Meta"])

    # USUÁRIOS
    with tab1:
        u = st.text_input("Usuário novo", key="novo_user")
        email = st.text_input("Email")
        s = st.text_input("Senha", type="password")
        nivel = st.selectbox("Perfil", ["user", "admin"])

        if st.button("Criar"):
            banco.criar_usuario(u, email, s, nivel)
            st.success("Criado")

        dados = banco.listar_usuarios()

        for d in dados:
            col1, col2 = st.columns([3,1])
            col1.write(d)

            if col2.button("Excluir", key=d[0]):
                banco.excluir_usuario(d[0])
                st.rerun()

    # SALÁRIO
    with tab2:
        dados = banco.listar_usuarios()

        for d in dados:
            valor = st.number_input(
                f"Salário {d[0]}",
                value=float(d[2]),
                key="sal"+d[0]
            )

            if st.button(f"Salvar {d[0]}", key="b1"+d[0]):
                banco.atualizar_salario(d[0], valor)

    # META
    with tab3:
        dados = banco.listar_usuarios()

        for d in dados:
            valor = st.number_input(
                f"Meta {d[0]}",
                value=float(d[3]),
                key="meta"+d[0]
            )

            if st.button(f"Salvar meta {d[0]}", key="b2"+d[0]):
                banco.atualizar_meta(d[0], valor)
