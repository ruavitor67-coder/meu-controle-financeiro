import streamlit as st
import pandas as pd
import plotly.express as px
import banco 
from io import BytesIO

def f_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Gestão Financeira Pro", page_icon="💰", layout="wide")
banco.criar_tabelas()

# --- ESTILIZAÇÃO CSS (CORES VIVAS) ---
st.markdown("""
    <style>
    /* Cor de fundo e fontes */
    .stApp { background-color: #0E1117; }
    
    /* Cartões de Métricas */
    [data-testid="stMetricValue"] { color: #00FFAA !important; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #FFFFFF !important; }
    
    /* Botões Vibrantes */
    .stButton>button {
        background-color: #6200EE;
        color: white;
        border-radius: 10px;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #FF00FF; border: none; color: white; }
    
    /* Barras de Progresso Customizadas */
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #00FFAA, #00FF00); }
    
    /* Títulos */
    h1, h2, h3 { color: #FF00FF !important; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

if 'logado' not in st.session_state:
    st.session_state.logado, st.session_state.user, st.session_state.role = False, "", ""
if 'editando_salario' not in st.session_state:
    st.session_state.editando_salario = False

# --- LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        role = banco.validar_login(u, p)
        if role:
            st.session_state.logado, st.session_state.user, st.session_state.role = True, u, role
            st.rerun()
    st.stop()

# --- SIDEBAR ---
st.sidebar.title(f"👤 {st.session_state.user.upper()}")
sal_atual = banco.buscar_salario(st.session_state.user)

if not st.session_state.editando_salario:
    col_v, col_b = st.sidebar.columns([1.5, 1])
    col_v.write(f"Salário: **{f_moeda(sal_atual)}**")
    if col_b.button("Alterar"):
        st.session_state.editando_salario = True
        st.rerun()
else:
    n_sal = st.sidebar.number_input("Novo Valor:", value=float(sal_atual))
    if st.sidebar.button("Salvar Salário"):
        banco.atualizar_salario(st.session_state.user, n_sal)
        st.session_state.editando_salario = False
        st.rerun()

st.sidebar.divider()
menu = ["📊 Dashboard", "💸 Lançar Gasto", "📥 Importar Extrato", "🎯 Metas"]
if st.session_state.user.lower() == 'vitim' or st.session_state.role == 'admin':
    menu.append("👥 Usuários")
escol
