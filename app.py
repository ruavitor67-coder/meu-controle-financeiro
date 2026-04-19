import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

def f_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Gestão Financeira Pro", page_icon="📈", layout="wide")
banco.criar_tabelas()

# --- CSS PROFISSIONAL ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; }
    h1, h2, h3 { color: #E0E0E0 !important; }
    [data-testid="stMetricValue"] { color: #10B981 !important; font-weight: 600; }
    .stButton>button {
        background-color: #1E3A8A; color: white; border-radius: 6px;
        border: none; transition: 0.2s;
    }
    .stButton>button:hover { background-color: #3B82F6; color: white; }
    </style>
    """, unsafe_allow_html=True)

if 'logado' not in st.session_state:
    st.session_state.logado, st.session_state.user, st.session_state.role = False, "", ""
if 'editando_salario' not in st.session_state:
    st.session_state.editando_salario = False

# --- LOGIN ---
if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center;'>🔐 Acesso Profissional</h1>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1,1.2,1])
    with col2:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            role = banco.validar_login(u, p)
            if role:
                st.session_state.logado, st.session_state.user, st.session_state.role = True, u, role
                st.rerun()
            else: st.error("Erro de autenticação.")
    st.stop()

# --- SIDEBAR (ONDE SE ALTERA O SALÁRIO) ---
st.sidebar.markdown(f"### 👤 {st.session_state.user.upper()}")
sal_atual = banco.buscar_salario(st.session_state.user)

if not st.session_state.editando_salario:
    st.sidebar.write(f"Salário Atual: **{f_moeda(sal_atual)}**")
    if st.sidebar.button("Alterar Salário"):
        st.session_state.editando_salario = True
        st.rerun()
else:
    n_sal = st.sidebar.number_input("Definir Novo Valor:", value=float(sal_atual))
    if st.sidebar.button("Salvar Alteração"):
        banco.atualizar_salario(st.session_state.user, n_sal)
        st.session_state.editando_salario = False
        st.rerun()

st.sidebar.divider()
menu = ["📊 Dashboard", "💸 Lançamentos", "🎯 Metas"]
if st.session_state.user.lower() == 'vitim' or st.session_state.role == 'admin':
    menu.append("👥 Administração")
escolha = st.sidebar.selectbox("Navegação", menu)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---
if escolha == "📊 Dashboard":
    st.header("📊 Resumo de Contas")
    df = banco.buscar_gastos(st.session_state.user)
    if not df.empty:
        total = df['valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Orçamento Disponível", f_moeda(sal_atual))
        c2.metric("Despesas Totais", f_moeda(total), delta=f"-{f_moeda(total)}", delta_color="inverse")
        c3.metric("Saldo Líquido", f_moeda(sal_atual - total))
        st.plotly_chart(px.pie(df, values='valor', names='categoria', hole=0.5, template="plotly_dark"), use_container_width=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Sem lançamentos para exibir.")

elif escolha == "💸 Lançamentos":
    st.header("💸 Novo Lançamento")
    with st.form("lanc"):
        d = st.date_input("Data")
        cat = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
        desc = st.text_input("Descrição")
        val = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("REGISTRAR"):
            banco.salvar_gasto(st.session_state.user, d, cat, desc, val)
            st.success("Salvo com sucesso!")

elif escolha == "👥 Administração":
    st.header("👥 Gestão de Usuários")
    with st.expander("➕ Novo Usuário"):
        c1, c2, c3 = st.columns(3)
        nu = c1.text_input("Nome")
        np = c2.text_input("Senha", type="password")
        nr = c3.selectbox("Nível", ["user", "admin"])
        if st.button("Criar"):
            if banco.adicionar_usuario(nu, np, nr): st.rerun()
    
    df_u = banco.listar_usuarios()
    st.dataframe(df_u, use_container_width=True)
    
    # Opção de exclusão
    u_del = st.selectbox("Remover Usuário:", [u for u in df_u['usuario'].tolist() if u.lower() != 'vitim'])
    if st.button("Excluir Permanente", type="primary"):
        if banco.deletar_usuario(u_del): st.rerun()
