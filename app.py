import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

def f_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Financeiro Premium", page_icon="📈", layout="wide")
banco.criar_tabelas()

# --- CSS PROFISSIONAL ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; }
    h1, h2, h3 { color: #E0E0E0 !important; font-family: 'Inter', sans-serif; }
    [data-testid="stMetricValue"] { color: #10B981 !important; font-weight: 600; }
    .stButton>button {
        background-color: #1E3A8A; color: white; border-radius: 6px;
        border: none; font-weight: 500; transition: 0.2s;
    }
    .stButton>button:hover { background-color: #3B82F6; color: white; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #059669, #10B981); }
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
        if st.button("ACESSAR SISTEMA"):
            role = banco.validar_login(u, p)
            if role:
                st.session_state.logado, st.session_state.user, st.session_state.role = True, u, role
                st.rerun()
            else: st.error("Usuário ou senha inválidos.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.markdown(f"### 👤 {st.session_state.user.upper()}")
sal_atual = banco.buscar_salario(st.session_state.user)

if not st.session_state.editando_salario:
    st.sidebar.write(f"Salário: **{f_moeda(sal_atual)}**")
    if st.sidebar.button("Editar Salário"):
        st.session_state.editando_salario = True
        st.rerun()
else:
    n_sal = st.sidebar.number_input("Novo Valor:", value=float(sal_atual))
    if st.sidebar.button("Salvar"):
        banco.atualizar_salario(st.session_state.user, n_sal)
        st.session_state.editando_salario = False
        st.rerun()

st.sidebar.divider()
menu = ["📊 Dashboard", "💸 Lançamentos", "🎯 Metas"]
if st.session_state.role == 'admin':
    menu.append("👥 Administração")
escolha = st.sidebar.selectbox("Navegação", menu)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---
if escolha == "📊 Dashboard":
    st.header("📊 Resumo de Performance")
    df = banco.buscar_gastos(st.session_state.user)
    if not df.empty:
        total = df['valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Orçamento", f_moeda(sal_atual))
        c2.metric("Despesas", f_moeda(total), delta=f"-{f_moeda(total)}", delta_color="inverse")
        c3.metric("Saldo Líquido", f_moeda(sal_atual - total))
        st.plotly_chart(px.pie(df, values='valor', names='categoria', hole=0.5, template="plotly_dark"), use_container_width=True)
        st.dataframe(df.sort_values(by='data', ascending=False), use_container_width=True)
    else:
        st.info("Nenhum gasto registrado.")

elif escolha == "💸 Lançamentos":
    st.header("💸 Novo Registro")
    with st.form("add_gasto"):
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
    with st.expander("➕ Adicionar Novo"):
        c1, c2, c3 = st.columns(3)
        nu = c1.text_input("Nome")
        np = c2.text_input("Senha", type="password")
        nr = c3.selectbox("Permissão", ["user", "admin"])
        if st.button("Criar Conta"):
            if banco.adicionar_usuario(nu, np, nr): st.rerun()
            else: st.error("Erro ao criar usuário.")
    
    df_u = banco.listar_usuarios()
    st.dataframe(df_u, use_container_width=True)
    
    u_del = st.selectbox("Remover Usuário:", [u for u in df_u['usuario'].tolist() if u != 'admin'])
    if st.button("Excluir Permanente", type="primary"):
        if banco.deletar_usuario(u_del): st.rerun()
