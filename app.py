import streamlit as st
import pandas as pd
import plotly.express as px
import banco 
from io import BytesIO

def f_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Gestão Financeira", page_icon="💰", layout="wide")
banco.criar_tabelas()

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

# Lógica do botão Alterar Salário
sal_atual = banco.buscar_salario(st.session_state.user)
if not st.session_state.editando_salario:
    col_v, col_b = st.sidebar.columns([2, 1])
    col_v.write(f"Atual: **{f_moeda(sal_atual)}**")
    if col_b.button("Alterar"):
        st.session_state.editando_salario = True
        st.rerun()
else:
    n_sal = st.sidebar.number_input("Novo Valor:", value=float(sal_atual))
    c1, c2 = st.sidebar.columns(2)
    if c1.button("Salvar"):
        banco.atualizar_salario(st.session_state.user, n_sal)
        st.session_state.editando_salario = False
        st.rerun()
    if c2.button("Cancelar"):
        st.session_state.editando_salario = False
        st.rerun()

st.sidebar.divider()
# Restaurando o Menu Completo
opcoes = ["📊 Dashboard", "💸 Gastos", "🎯 Metas"]
if st.session_state.role == 'admin':
    opcoes.append("👥 Usuários")

escolha = st.sidebar.radio("Navegação", opcoes)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---

if escolha == "📊 Dashboard":
    st.header("📊 Painel de Controle")
    df = banco.buscar_gastos(st.session_state.user)
    
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        # Filtros de Data
        c_ano, c_mes = st.columns(2)
        ano = c_ano.selectbox("Ano", ["Todos"] + list(df['data'].dt.year.unique()))
        df_f = df.copy()
        if ano != "Todos":
            df_f = df_f[df_f['data'].dt.year == ano]
        
        # Métricas e Exportação
        total = df_f['valor'].sum()
        st.metric("Total Gasto no Período", f_moeda(total))
        
        # Botão Excel
        output = BytesIO()
        df_f.to_excel(output, index=False)
        st.download_button("📥 Baixar Relatório Excel", output.getvalue(), "gastos.xlsx")
        
        st.plotly_chart(px.pie(df_f, values='valor', names='categoria', hole=0.4))
    else:
        st.info("Nenhum gasto encontrado.")

elif escolha == "💸 Gastos":
    st.header("💸 Lançar Gasto")
    with st.form("add"):
        data = st.date_input("Data")
        cat = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Fixos", "Outros"])
        desc = st.text_input("Descrição")
        val = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("Salvar"):
            banco.salvar_gasto(st.session_state.user, data, cat, desc, val)
            st.success("Gasto salvo!")

elif escolha == "🎯 Metas":
    st.header("🎯 Minhas Metas")
    cat_meta = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Fixos", "Outros"])
    valor_meta = st.number_input("Limite Mensal", min_value=0.0)
    if st.button("Definir Meta"):
        banco.definir_meta(st.session_state.user, cat_meta, valor_meta)
        st.success("Meta atualizada!")

elif escolha == "👥 Usuários":
    st.header("👥 Gestão de Usuários")
    df_u = banco.listar_usuarios()
    st.dataframe(df_u)
    u_del = st.selectbox("Selecionar Usuário para remover", [u for u in df_u['usuario'] if u != 'vitim'])
    if st.button("Excluir Usuário", type="primary"):
        banco.deletar_usuario(u_del)
        st.rerun()
