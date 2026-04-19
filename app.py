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

# Melhoria Visual do Salário
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
menu = ["📊 Dashboard", "💸 Lançar Gasto", "🎯 Metas"]
if st.session_state.role == 'admin':
    menu.append("👥 Usuários")
escolha = st.sidebar.selectbox("Ir para:", menu)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---

if escolha == "📊 Dashboard":
    st.header("📊 Resumo Financeiro")
    df = banco.buscar_gastos(st.session_state.user)
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        # Filtros e Exportação
        c_ano, c_mes = st.columns(2)
        ano = c_ano.selectbox("Ano", ["Todos"] + list(df['data'].dt.year.unique()))
        df_f = df.copy()
        if ano != "Todos": df_f = df_f[df_f['data'].dt.year == ano]
        
        total = df_f['valor'].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Salário", f_moeda(sal_atual))
        m2.metric("Total Gasto", f_moeda(total), delta_color="inverse")
        m3.metric("Saldo", f_moeda(sal_atual - total))

        output = BytesIO()
        df_f.to_excel(output, index=False)
        st.download_button("📥 Baixar Excel", output.getvalue(), "gastos.xlsx")
        st.plotly_chart(px.pie(df_f, values='valor', names='categoria', hole=0.4))
    else:
        st.info("Lance gastos para ver o resumo.")

elif escolha == "💸 Lançar Gasto":
    st.header("💸 Novo Gasto")
    with st.form("add_gasto", clear_on_submit=True):
        c1, c2 = st.columns(2)
        data = c1.date_input("Data")
        cat = c2.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
        if st.form_submit_button("Salvar"):
            banco.salvar_gasto(st.session_state.user, data, cat, desc, valor)
            st.success("Salvo!")

elif escolha == "👥 Usuários":
    st.header("👥 Gestão de Usuários")
    df_u = banco.listar_usuarios()
    st.dataframe(df_u, use_container_width=True)
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        u_sel = st.selectbox("Mudar Senha:", df_u['usuario'].tolist(), key="u_pw")
        n_pw = st.text_input("Nova Senha", type="password")
        if st.button("Confirmar Senha"):
            banco.alterar_senha_usuario(u_sel, n_pw)
            st.success("Senha alterada!")
    with col_b:
        u_cargo = st.selectbox("Mudar Cargo:", df_u['usuario'].tolist(), key="u_rl")
        n_rl = st.radio("Nível:", ["user", "admin"])
        if st.button("Confirmar Cargo"):
            banco.alterar_nivel_usuario(u_cargo, n_rl)
            st.rerun()
    with col_c:
        deletar_lista = [u for u in df_u['usuario'].tolist() if u.lower() != 'vitim']
        u_del = st.selectbox("Remover:", deletar_lista, key="u_del")
        if st.button("Confirmar Exclusão", type="primary"):
            banco.deletar_usuario(u_del)
            st.rerun()

elif escolha == "🎯 Metas":
    st.header("🎯 Metas")
    cat_meta = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
    v_meta = st.number_input("Limite", min_value=0.0)
    if st.button("Salvar Meta"):
        banco.definir_meta(st.session_state.user, cat_meta, v_meta)
        st.success("Meta definida!")
