import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

def f_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Gestão Financeira Pro", page_icon="📈", layout="wide")
banco.criar_tabelas()

# --- CSS PROFISSIONAL AZUL ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; }
    h1, h2, h3 { color: #E0E0E0 !important; font-family: 'Inter', sans-serif; }
    [data-testid="stMetricValue"] { color: #10B981 !important; font-weight: 600; }
    .stButton>button {
        background-color: #1E3A8A; color: white; border-radius: 6px;
        border: none; font-weight: 500; transition: 0.2s; width: 100%;
    }
    .stButton>button:hover { background-color: #3B82F6; color: white; }
    .stExpander { border: 1px solid #334155; border-radius: 6px; background-color: #1A1F26; }
    </style>
    """, unsafe_allow_html=True)

if 'logado' not in st.session_state:
    st.session_state.logado, st.session_state.user, st.session_state.role = False, "", ""
if 'editando_salario' not in st.session_state:
    st.session_state.editando_salario = False

# --- LOGIN ---
if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center;'>🔐 Acesso Restrito</h1>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1,1.2,1])
    with col2:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            role = banco.validar_login(u, p)
            if role:
                st.session_state.logado, st.session_state.user, st.session_state.role = True, u, role
                st.rerun()
            else: st.error("Credenciais inválidas.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.markdown(f"### 👤 {st.session_state.user.upper()}")
sal_atual = banco.buscar_salario(st.session_state.user)

if not st.session_state.editando_salario:
    st.sidebar.write(f"Salário: **{f_moeda(sal_atual)}**")
    if st.sidebar.button("Editar Valor"):
        st.session_state.editando_salario = True
        st.rerun()
else:
    n_sal = st.sidebar.number_input("Novo Salário:", value=float(sal_atual))
    if st.sidebar.button("Salvar"):
        banco.atualizar_salario(st.session_state.user, n_sal)
        st.session_state.editando_salario = False
        st.rerun()

st.sidebar.divider()
menu = ["📊 Dashboard", "💸 Lançamentos", "🎯 Metas"]
if st.session_state.role == 'admin':
    menu.append("👥 Administração")
escolha = st.sidebar.selectbox("Módulo", menu)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---
if escolha == "📊 Dashboard":
    st.header("📊 Resumo Financeiro")
    df = banco.buscar_gastos(st.session_state.user)
    if not df.empty:
        total = df['valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Orçamento", f_moeda(sal_atual))
        c2.metric("Gasto Total", f_moeda(total), delta=f"-{f_moeda(total)}", delta_color="inverse")
        c3.metric("Livre", f_moeda(sal_atual - total))
        st.plotly_chart(px.pie(df, values='valor', names='categoria', hole=0.5, template="plotly_dark"), use_container_width=True)
        st.dataframe(df.sort_values(by='data', ascending=False), use_container_width=True)
    else:
        st.info("Nenhum dado lançado ainda.")

elif escolha == "💸 Lançamentos":
    st.header("💸 Registrar Gasto")
    with st.form("form_gasto"):
        c1, c2 = st.columns(2)
        d = c1.date_input("Data")
        cat = c2.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
        desc = st.text_input("Descrição")
        val = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("REGISTRAR"):
            banco.salvar_gasto(st.session_state.user, d, cat, desc, val)
            st.success("Salvo!")

elif escolha == "👥 Administração":
    st.header("👥 Gestão de Usuários")
    
    with st.expander("➕ Adicionar Novo Usuário"):
        c1, c2, c3 = st.columns(3)
        nu = c1.text_input("Login")
        np = c2.text_input("Senha", type="password")
        nr = c3.selectbox("Nível", ["user", "admin"])
        if st.button("Criar"):
            if nu and np:
                if banco.adicionar_usuario(nu, np, nr): st.rerun()
                else: st.error("Usuário já existe.")
    
    st.divider()
    df_u = banco.listar_usuarios()
    st.subheader("📋 Usuários")
    st.dataframe(df_u, use_container_width=True)
    
    st.divider()
    st.subheader("⚙️ Ações")
    c_s, c_c, c_d = st.columns(3)
    u_list = df_u['usuario'].tolist()

    with c_s:
        u_sel_s = st.selectbox("Senha de:", u_list, key="us")
        n_s = st.text_input("Nova Senha:", type="password", key="ns")
        if st.button("Mudar Senha"):
            banco.alterar_senha_usuario(u_sel_s, n_s)
            st.success("Alterado!")

    with c_c:
        u_sel_c = st.selectbox("Cargo de:", u_list, key="uc")
        n_n = st.radio("Nível:", ["user", "admin"], horizontal=True, key="nn")
        if st.button("Mudar Nível"):
            banco.alterar_nivel_usuario(u_sel_c, n_n)
            st.rerun()

    with c_d:
        # Pega admin fixo dos secrets para proteger
        adm_f = st.secrets.get("ADMIN_USER", "admin")
        u_sel_d = st.selectbox("Excluir:", [u for u in u_list if u != adm_f], key="ud")
        if st.button("EXCLUIR AGORA", type="primary"):
            if banco.deletar_usuario(u_sel_d): st.rerun()
