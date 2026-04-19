import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

def f_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Finanças Neon Pro", page_icon="💰", layout="wide")
banco.criar_tabelas()

# --- CSS PARA CORES VIVAS E INTERFACE MODERNA ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    [data-testid="stMetricValue"] { color: #00FFAA !important; font-size: 32px; font-weight: bold; }
    .stButton>button {
        background-color: #6200EE; color: white; border-radius: 12px;
        width: 100%; border: none; font-weight: bold; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #FF00FF; transform: scale(1.02); }
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
    st.title("🔐 Acesso Restrito")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            role = banco.validar_login(u, p)
            if role:
                st.session_state.logado, st.session_state.user, st.session_state.role = True, u, role
                st.rerun()
            else:
                st.error("Dados incorretos.")
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
    n_sal = st.sidebar.number_input("Novo Valor:", value=float(sal_atual))
    if st.sidebar.button("Confirmar Salário"):
        banco.atualizar_salario(st.session_state.user, n_sal)
        st.session_state.editando_salario = False
        st.rerun()

st.sidebar.divider()
menu = ["📊 Dashboard", "💸 Novo Gasto", "🎯 Metas Mensais", "📥 Importação"]
if st.session_state.user.lower() == 'vitim' or st.session_state.role == 'admin':
    menu.append("👥 Gestão de Usuários")
escolha = st.sidebar.selectbox("Navegação", menu)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---

if escolha == "📊 Dashboard":
    st.header("📊 Painel de Controle")
    df = banco.buscar_gastos(st.session_state.user)
    df_metas = banco.buscar_metas(st.session_state.user)
    
    if not df.empty:
        total = df['valor'].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Salário", f_moeda(sal_atual))
        m2.metric("Gasto Total", f_moeda(total), delta="-Saldo", delta_color="inverse")
        m3.metric("Livre", f_moeda(sal_atual - total))
        
        st.divider()
        st.subheader("🎯 Progresso das Metas")
        if not df_metas.empty:
            for _, m in df_metas.iterrows():
                gasto_c = df[df['categoria'] == m['categoria']]['valor'].sum()
                perc = min(gasto_c / m['limite'], 1.0) if m['limite'] > 0 else 0
                
                col_t, col_b = st.columns([1, 4])
                col_t.write(f"**{m['categoria']}**")
                if perc >= 1.0:
                    col_b.error(f"Estourou! {f_moeda(gasto_c)}")
                else:
                    col_b.progress(perc)
                    st.caption(f"Gasto {f_moeda(gasto_c)} de {f_moeda(m['limite'])}")
        
        st.divider()
        fig = px.pie(df, values='valor', names='categoria', hole=0.5)
        fig.update_layout(template="plotly_dark", title="Gastos por Categoria")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df.sort_values(by='id', ascending=False), use_container_width=True)
    else:
        st.info("Lance gastos para gerar o dashboard.")

elif escolha == "💸 Novo Gasto":
    st.header("💸 Lançar Despesa")
    with st.form("form_gasto"):
        c1, c2 = st.columns(2)
        d = c1.date_input("Data")
        cat = c2.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
        desc = st.text_input("O que foi?")
        val = st.number_input("Quanto custou?", min_value=0.0)
        if st.form_submit_button("SALVAR"):
            banco.salvar_gasto(st.session_state.user, d, cat, desc, val)
            st.balloons()
            st.success("Registrado!")

elif escolha == "👥 Gestão de Usuários":
    st.header("👥 Painel Admin")
    df_u = banco.listar_usuarios()
    st.dataframe(df_u, use_container_width=True)
    
    col_a, col_b, col_c = st.columns(3)
    u_lista = df_u['usuario'].tolist()
    
    with col_a:
        u_sel = st.selectbox("Usuário:", u_lista, key="u1")
        n_pw = st.text_input("Nova Senha", type="password")
        if st.button("Mudar Senha"):
            banco.alterar_senha_usuario(u_sel, n_pw)
            st.success("Senha alterada!")
            
    with col_b:
        u_rl = st.selectbox("Usuário:", u_lista, key="u2")
        n_rl = st.radio("Cargo:", ["user", "admin"])
        if st.button("Mudar Nível"):
            if banco.alterar_nivel_usuario(u_rl, n_rl): st.rerun()
            
    with col_c:
        u_del = st.selectbox("Remover:", [u for u in u_lista if u.lower() != 'vitim'], key="u3")
        if st.button("CONFIRMAR EXCLUSÃO", type="primary"):
            if banco.deletar_usuario(u_del):
                st.success("Removido!")
                st.rerun()

elif escolha == "🎯 Metas Mensais":
    st.header("🎯 Definir Limites")
    cat_m = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
    lim_m = st.number_input("Valor Limite", min_value=0.0)
    if st.button("Salvar Meta"):
        banco.definir_meta(st.session_state.user, cat_m, lim_m)
        st.success("Meta configurada!")
