import streamlit as st
import plotly.express as px
from datetime import date
import banco

st.set_page_config(page_title="Financeiro PRO", layout="wide")

banco.criar_tabelas()

# CONTROLE
if "logado" not in st.session_state:
    st.session_state.logado = False

if "pagina" not in st.session_state:
    st.session_state.pagina = "dashboard"

if "menu" not in st.session_state:
    st.session_state.menu = True

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

    st.markdown("---")
    st.subheader("🔑 Recuperar senha")

    u2 = st.text_input("Usuário")
    s2 = st.text_input("Nova senha", type="password")

    if st.button("Redefinir"):
        banco.redefinir_senha(u2, s2)
        st.success("Senha redefinida")

# SISTEMA
else:
    user = st.session_state.user

    # SIDEBAR
    if st.sidebar.button("☰ Menu"):
        st.session_state.menu = not st.session_state.menu

    if st.session_state.menu:

        salario = banco.buscar_salario(user)
        meta = banco.buscar_meta(user)

        with st.sidebar.expander("💰 Salário"):
            v = st.number_input("Seu salário", value=float(salario))
            if st.button("Salvar Salário"):
                banco.atualizar_salario(user, v)
                st.rerun()

        with st.sidebar.expander("🎯 Meta"):
            m = st.number_input("Meta", value=float(meta))
            if st.button("Salvar Meta"):
                banco.atualizar_meta(user, m)
                st.rerun()

        with st.sidebar.expander("📊 Dashboard"):
            if st.button("Abrir"):
                st.session_state.pagina = "dashboard"
                st.rerun()

        with st.sidebar.expander("💸 Gasto"):
            if st.button("Novo"):
                st.session_state.pagina = "gasto"
                st.rerun()

        with st.sidebar.expander("⚙️ Config"):
            if st.button("Abrir Config"):
                st.session_state.pagina = "config"
                st.rerun()

        if st.session_state.nivel == "admin":
            with st.sidebar.expander("👤 Admin"):
                if st.button("Abrir Admin"):
                    st.session_state.pagina = "admin"
                    st.rerun()

        if st.sidebar.button("Sair"):
            st.session_state.logado = False
            st.rerun()

    # DADOS
    df = banco.buscar_gastos(user)
    pagina = st.session_state.pagina

    # DASHBOARD
    if pagina == "dashboard":
        st.title("📊 Dashboard")

        if not df.empty:
            df['data'] = df['data'].astype('datetime64[ns]')
            df['mes'] = df['data'].dt.to_period('M').astype(str)

            total = df['valor'].sum()

            c1,c2,c3 = st.columns(3)
            c1.metric("Salário", f"R$ {salario:.2f}")
            c2.metric("Gastos", f"R$ {total:.2f}")
            c3.metric("Saldo", f"R$ {salario-total:.2f}")

            st.plotly_chart(px.pie(df, values='valor', names='categoria'))

            df_mes = df.groupby('mes')['valor'].sum().reset_index()
            st.plotly_chart(px.bar(df_mes, x='mes', y='valor'))

    # GASTO
    elif pagina == "gasto":
        st.title("💸 Novo Gasto")

        with st.form("f"):
            d = st.date_input("Data", date.today())
            cat = st.selectbox("Categoria", ["Alimentação","Transporte","Moradia","Lazer"])
            desc = st.text_input("Descrição")
            val = st.number_input("Valor")
            stt = st.selectbox("Status", ["Pago","Pendente"])

            if st.form_submit_button("Salvar"):
                banco.salvar_gasto(user,d,cat,desc,val,stt)
                st.rerun()

    # CONFIG
    elif pagina == "config":
        st.title("⚙️ Configurações")

        for _,r in df.iterrows():
            c1,c2 = st.columns([6,1])
            c1.write(f"{r['data']} | {r['descricao']} | R$ {r['valor']}")
            if c2.button("🗑️", key=r['id']):
                banco.deletar_gasto(r['id'])
                st.rerun()

    # ADMIN
    elif pagina == "admin":
        st.title("👥 Admin")

        dfu = banco.listar_usuarios()

        st.dataframe(dfu)

        for _,r in dfu.iterrows():
            with st.expander(r['usuario']):
                s = st.text_input("Senha", type="password", key=r['usuario'])
                if st.button("Alterar", key="a"+r['usuario']):
                    banco.alterar_senha(r['usuario'], s)
