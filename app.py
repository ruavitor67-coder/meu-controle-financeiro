import streamlit as st
import pandas as pd
import plotly.express as px
import banco 
from io import BytesIO

def f_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Gestão Financeira Pro", page_icon="💰", layout="wide")
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
sal_atual = banco.buscar_salario(st.session_state.user)

st.sidebar.subheader("💵 Salário")
if not st.session_state.editando_salario:
    col_v, col_b = st.sidebar.columns([1.5, 1])
    col_v.write(f"**{f_moeda(sal_atual)}**")
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
menu = ["📊 Dashboard", "💸 Lançar Gasto", "📥 Importar Extrato", "🎯 Metas"]

# Apenas Vitim ou Admins vêem a aba de Usuários
if st.session_state.user.lower() == 'vitim' or st.session_state.role == 'admin':
    menu.append("👥 Usuários")

escolha = st.sidebar.selectbox("Menu:", menu)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---

if escolha == "📊 Dashboard":
    st.header("📊 Resumo Financeiro")
    df = banco.buscar_gastos(st.session_state.user)
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        pago = df[df['status'] == 'Pago']['valor'].sum()
        pendente = df[df['status'] == 'Pendente']['valor'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Salário", f_moeda(sal_atual))
        m2.metric("Total Pago", f_moeda(pago))
        m3.metric("Pendente", f_moeda(pendente), delta_color="inverse")
        
        st.dataframe(df, use_container_width=True)
        
        st.subheader("⚙️ Ações Rápidas")
        id_st = st.number_input("ID do Gasto para mudar status:", min_value=0, step=1)
        if st.button("Inverter Status (Pago/Pendente)"):
            try:
                atual = df[df['id'] == id_st]['status'].values[0]
                novo = "Pendente" if atual == "Pago" else "Pago"
                banco.atualizar_status_gasto(id_st, novo)
                st.rerun()
            except: st.error("ID não encontrado.")
    else:
        st.info("Lance gastos para começar.")

elif escolha == "💸 Lançar Gasto":
    st.header("💸 Novo Lançamento")
    with st.form("add_gasto"):
        d = st.date_input("Data")
        c = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
        ds = st.text_input("Descrição")
        v = st.number_input("Valor", min_value=0.0)
        s = st.radio("Status:", ["Pago", "Pendente"], horizontal=True)
        if st.form_submit_button("Salvar"):
            banco.salvar_gasto(st.session_state.user, d, c, ds, v, s)
            st.success("Salvo!")

elif escolha == "👥 Usuários":
    st.header("👥 Gestão de Usuários")
    df_u = banco.listar_usuarios()
    st.dataframe(df_u, use_container_width=True)
    
    col_a, col_b, col_c = st.columns(3)
    u_lista = df_u['usuario'].tolist()
    
    with col_a:
        st.subheader("🔑 Senha")
        u_pw = st.selectbox("Usuário:", u_lista, key="u_pw")
        n_pw = st.text_input("Nova Senha", type="password", key="n_pw")
        if st.button("Confirmar Senha"):
            banco.alterar_senha_usuario(u_pw, n_pw)
            st.success("Senha atualizada!")

    with col_b:
        st.subheader("🛡️ Cargo")
        u_rl = st.selectbox("Usuário:", u_lista, key="u_rl")
        n_rl = st.radio("Nível:", ["user", "admin"], key="n_rl")
        if st.button("Confirmar Nível"):
            if banco.alterar_nivel_usuario(u_rl, n_rl): st.rerun()
            else: st.error("Ação bloqueada.")

    with col_c:
        st.subheader("🗑️ Remover")
        lista_del = [u for u in u_lista if u.lower().strip() != 'vitim']
        if lista_del:
            u_del = st.selectbox("Escolha quem remover:", lista_del, key="u_del")
            if st.button("Confirmar Exclusão", type="primary"):
                if banco.deletar_usuario(u_del):
                    st.success("Removido!")
                    st.rerun()
        else:
            st.info("Apenas você está no sistema.")

elif escolha == "📥 Importar Extrato":
    st.header("📥 Importar Dados")
    arq = st.file_uploader("Subir Excel/CSV", type=['csv', 'xlsx'])
    if arq:
        df_imp = pd.read_csv(arq) if arq.name.endswith('.csv') else pd.read_excel(arq)
        if st.button("Confirmar Importação"):
            for _, r in df_imp.iterrows():
                banco.salvar_gasto(st.session_state.user, r['data'], r['categoria'], r['descricao'], r['valor'])
            st.success("Importado!")

elif escolha == "🎯 Metas":
    st.header("🎯 Metas")
    cat_m = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
    v_m = st.number_input("Limite Mensal", min_value=0.0)
    if st.button("Definir Meta"):
        banco.definir_meta(st.session_state.user, cat_m, v_m)
        st.success("Meta salva!")
