import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

def f_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Financeiro Premium", page_icon="📈", layout="wide")
banco.criar_tabelas()

# --- CSS PROFISSIONAL DARK MODERN ---
st.markdown("""
    <style>
    /* Fundo Dark Sóbrio */
    .stApp { background-color: #0B0E14; }
    
    /* Títulos em Branco e Ciano */
    h1, h2, h3 { color: #E0E0E0 !important; font-family: 'Inter', sans-serif; letter-spacing: -0.5px; }
    
    /* Métricas Profissionais (Azul Esmeralda) */
    [data-testid="stMetricValue"] { color: #2EE59D !important; font-weight: 600; font-size: 32px; }
    [data-testid="stMetricLabel"] { color: #9DA5B1 !important; }

    /* Botões em Azul Royal Profundo */
    .stButton>button {
        background-color: #1E3A8A; color: #FFFFFF; border-radius: 6px;
        padding: 0.5rem 1rem; border: none; font-weight: 500; transition: 0.2s;
    }
    .stButton>button:hover { background-color: #3B82F6; border: none; color: white; }
    
    /* Input Fields */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #1A1F26; color: white; border: 1px solid #334155;
    }

    /* Barras de Progresso Esmeralda */
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #10B981, #34D399); }
    
    /* Tabelas */
    .styled-table { background-color: #1A1F26; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'logado' not in st.session_state:
    st.session_state.logado, st.session_state.user, st.session_state.role = False, "", ""
if 'editando_salario' not in st.session_state:
    st.session_state.editando_salario = False

# --- LOGIN ---
if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center;'>🔐 Acesso Restrito</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("LOGAR NO SISTEMA"):
            role = banco.validar_login(u, p)
            if role:
                st.session_state.logado, st.session_state.user, st.session_state.role = True, u, role
                st.rerun()
            else: st.error("Acesso negado.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.markdown(f"### 👤 {st.session_state.user.upper()}")
sal_atual = banco.buscar_salario(st.session_state.user)

if not st.session_state.editando_salario:
    st.sidebar.write(f"Salário Mensal: **{f_moeda(sal_atual)}**")
    if st.sidebar.button("Editar Salário"):
        st.session_state.editando_salario = True
        st.rerun()
else:
    n_sal = st.sidebar.number_input("Valor:", value=float(sal_atual))
    if st.sidebar.button("Confirmar"):
        banco.atualizar_salario(st.session_state.user, n_sal)
        st.session_state.editando_salario = False
        st.rerun()

st.sidebar.divider()
menu = ["📊 Dashboard", "💸 Lançamentos", "🎯 Gestão de Metas", "📥 Importação"]
if st.session_state.user.lower() == 'vitim' or st.session_state.role == 'admin':
    menu.append("👥 Administração")
escolha = st.sidebar.selectbox("Módulos", menu)

if st.sidebar.button("Finalizar Sessão"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---

if escolha == "📊 Dashboard":
    st.header("📊 Painel de Performance Financeira")
    df = banco.buscar_gastos(st.session_state.user)
    df_metas = banco.buscar_metas(st.session_state.user)
    
    if not df.empty:
        total = df['valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Receita Disponível", f_moeda(sal_atual))
        c2.metric("Despesa Acumulada", f_moeda(total), delta=f"-{f_moeda(total)}", delta_color="inverse")
        c3.metric("Saldo Líquido", f_moeda(sal_atual - total))
        
        st.divider()
        st.subheader("🎯 Metas vs Realizado")
        if not df_metas.empty:
            for _, m in df_metas.iterrows():
                gasto_c = df[df['categoria'] == m['categoria']]['valor'].sum()
                perc = min(gasto_c / m['limite'], 1.0) if m['limite'] > 0 else 0
                
                col_t, col_b = st.columns([1, 4])
                col_t.markdown(f"**{m['categoria']}**")
                if perc >= 1.0:
                    col_b.error(f"Excedido: {f_moeda(gasto_c)}")
                else:
                    col_b.progress(perc)
                    st.caption(f"Consumo: {int(perc*100)}% de {f_moeda(m['limite'])}")
        
        st.divider()
        st.plotly_chart(px.pie(df, values='valor', names='categoria', hole=0.6, 
                             color_discrete_sequence=px.colors.qualitative.Safe), use_container_width=True)
        st.subheader("📋 Extrato Detalhado")
        st.dataframe(df.sort_values(by='data', ascending=False), use_container_width=True)
    else:
        st.info("Aguardando lançamentos para processar dados.")

elif escolha == "💸 Lançamentos":
    st.header("💸 Novo Lançamento de Gasto")
    with st.form("lancamento"):
        c1, c2 = st.columns(2)
        d = c1.date_input("Data da Operação")
        cat = c2.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
        desc = st.text_input("Descrição / Fornecedor")
        val = st.number_input("Valor da Transação", min_value=0.0)
        if st.form_submit_button("EFETIVAR LANÇAMENTO"):
            banco.salvar_gasto(st.session_state.user, d, cat, desc, val)
            st.success("Transação registrada com sucesso!")

elif escolha == "👥 Administração":
    st.header("👥 Painel de Gestão de Contas")
    
    with st.expander("➕ Adicionar Novo Colaborador", expanded=False):
        c1, c2, c3 = st.columns(3)
        novo_u = c1.text_input("Usuário")
        novo_p = c2.text_input("Senha Temporária", type="password")
        novo_n = c3.selectbox("Nível Hierárquico", ["user", "admin"])
        if st.button("CADASTRAR"):
            if banco.adicionar_usuario(novo_u, novo_p, novo_n):
                st.success("Conta criada!"); st.rerun()
            else: st.error("Falha ao criar: Usuário já existente.")

    st.divider()
    df_u = banco.listar_usuarios()
    st.dataframe(df_u, use_container_width=True)
    
    col_a, col_b, col_c = st.columns(3)
    u_lista = df_u['usuario'].tolist()
    
    with col_a:
        u_sel = st.selectbox("Ajustar Senha:", u_lista, key="u1")
        n_pw = st.text_input("Nova Senha", type="password")
        if st.button("Confirmar Alteração"):
            banco.alterar_senha_usuario(u_sel, n_pw); st.toast("Atualizado!")
            
    with col_b:
        u_rl = st.selectbox("Ajustar Cargo:", u_lista, key="u2")
        n_rl = st.radio("Novo Nível:", ["user", "admin"], horizontal=True)
        if st.button("Confirmar Cargo"):
            if banco.alterar_nivel_usuario(u_rl, n_rl): st.rerun()
            
    with col_c:
        u_del = st.selectbox("Remover Conta:", [u for u in u_lista if u.lower() != 'vitim'], key="u3")
        if st.button("DELETAR PERMANENTE", type="primary"):
            if banco.deletar_usuario(u_del): st.rerun()

elif escolha == "🎯 Gestão de Metas":
    st.header("🎯 Planejamento de Orçamento")
    cat_m = st.selectbox("Categoria de Controle", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
    lim_m = st.number_input("Limite de Gasto Mensal", min_value=0.0)
    if st.button("ESTABELECER META"):
        banco.definir_meta(st.session_state.user, cat_m, lim_m)
        st.success(f"Orçamento para {cat_m} definido.")
