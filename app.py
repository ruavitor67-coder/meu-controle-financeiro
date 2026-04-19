import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

def f_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Finanças Neon Pro", page_icon="💰", layout="wide")
banco.criar_tabelas()

# --- CSS NEON VIBRANTE ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    [data-testid="stMetricValue"] { color: #00FFAA !important; font-weight: bold; }
    .stButton>button {
        background-color: #6200EE; color: white; border-radius: 10px;
        border: none; transition: 0.3s; font-weight: bold;
    }
    .stButton>button:hover { background-color: #FF00FF; color: white; transform: scale(1.02); }
    h1, h2, h3 { color: #FF00FF !important; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #00FFAA, #00FF00); }
    </style>
    """, unsafe_allow_html=True)

if 'logado' not in st.session_state:
    st.session_state.logado, st.session_state.user, st.session_state.role = False, "", ""
if 'editando_salario' not in st.session_state:
    st.session_state.editando_salario = False

# --- LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Login Neon")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        role = banco.validar_login(u, p)
        if role:
            st.session_state.logado, st.session_state.user, st.session_state.role = True, u, role
            st.rerun()
    st.stop()

# --- SIDEBAR ---
st.sidebar.title(f"👤 {st.session_state.user.upper()}")
sal_atual = banco.buscar_salario(st.session_state.user)

if not st.session_state.editando_salario:
    st.sidebar.write(f"Salário: **{f_moeda(sal_atual)}**")
    if st.sidebar.button("Alterar Valor"):
        st.session_state.editando_salario = True
        st.rerun()
else:
    n_sal = st.sidebar.number_input("Novo Salário:", value=float(sal_atual))
    if st.sidebar.button("Salvar Salário"):
        banco.atualizar_salario(st.session_state.user, n_sal)
        st.session_state.editando_salario = False
        st.rerun()

st.sidebar.divider()
menu = ["📊 Dashboard", "💸 Lançar Gasto", "🎯 Metas", "📥 Importar"]
if st.session_state.user.lower() == 'vitim' or st.session_state.role == 'admin':
    menu.append("👥 Gestão de Usuários")
escolha = st.sidebar.selectbox("Menu", menu)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---

if escolha == "📊 Dashboard":
    st.header("📊 Inteligência Financeira")
    df = banco.buscar_gastos(st.session_state.user)
    df_metas = banco.buscar_metas(st.session_state.user)
    
    if not df.empty:
        total = df['valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Salário", f_moeda(sal_atual))
        c2.metric("Gasto Total", f_moeda(total), delta="-Gasto", delta_color="inverse")
        c3.metric("Livre", f_moeda(sal_atual - total))
        
        st.divider()
        st.subheader("🎯 Acompanhamento de Metas")
        if not df_metas.empty:
            for _, m in df_metas.iterrows():
                gasto_c = df[df['categoria'] == m['categoria']]['valor'].sum()
                perc = min(gasto_c / m['limite'], 1.0) if m['limite'] > 0 else 0
                st.write(f"**{m['categoria']}** ({f_moeda(gasto_c)} / {f_moeda(m['limite'])})")
                st.progress(perc)
        
        st.plotly_chart(px.pie(df, values='valor', names='categoria', hole=0.5, template="plotly_dark"))
        st.dataframe(df.sort_values(by='id', ascending=False), use_container_width=True)
    else:
        st.info("Lance gastos para ver dados.")

elif escolha == "💸 Lançar Gasto":
    st.header("💸 Novo Gasto")
    with st.form("add"):
        d = st.date_input("Data")
        cat = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
        desc = st.text_input("Descrição")
        val = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("SALVAR"):
            banco.salvar_gasto(st.session_state.user, d, cat, desc, val)
            st.balloons()
            st.success("Salvo!")

elif escolha == "👥 Gestão de Usuários":
    st.header("👥 Painel Admin")
    
    # --- VOLTOU: CRIAR USUÁRIO ---
    with st.expander("✨ Cadastrar Novo Usuário", expanded=False):
        c1, c2, c3 = st.columns(3)
        novo_u = c1.text_input("Nome")
        novo_p = c2.text_input("Senha", type="password")
        novo_n = c3.selectbox("Nível", ["user", "admin"])
        if st.button("CRIAR AGORA"):
            if banco.adicionar_usuario(novo_u, novo_p, novo_n):
                st.success("Criado!"); st.rerun()
            else: st.error("Erro ou usuário já existe.")

    st.divider()
    df_u = banco.listar_usuarios()
    st.dataframe(df_u, use_container_width=True)
    
    col_a, col_b, col_c = st.columns(3)
    u_lista = df_u['usuario'].tolist()
    
    with col_a:
        u_sel = st.selectbox("Senha de:", u_lista, key="u1")
        n_pw = st.text_input("Nova Senha", type="password")
        if st.button("Alterar Senha"):
            banco.alterar_senha_usuario(u_sel, n_pw); st.success("OK!")
            
    with col_b:
        u_rl = st.selectbox("Cargo de:", u_lista, key="u2")
        n_rl = st.radio("Nível:", ["user", "admin"])
        if st.button("Salvar Cargo"):
            if banco.alterar_nivel_usuario(u_rl, n_rl): st.rerun()
            
    with col_c:
        u_del = st.selectbox("Excluir:", [u for u in u_lista if u.lower() != 'vitim'], key="u3")
        if st.button("CONFIRMAR EXCLUSÃO", type="primary"):
            if banco.deletar_usuario(u_del): st.rerun()

elif escolha == "🎯 Metas":
    st.header("🎯 Definir Limites")
    cat_m = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
    lim_m = st.number_input("Limite", min_value=0.0)
    if st.button("SALVAR META"):
        banco.definir_meta(st.session_state.user, cat_m, lim_m)
        st.success("Meta salva!")
