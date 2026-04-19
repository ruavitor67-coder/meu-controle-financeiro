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
sal_atual = banco.buscar_salario(st.session_state.user)

if not st.session_state.editando_salario:
    col_v, col_b = st.sidebar.columns([1.5, 1])
    col_v.write(f"Salário: **{f_moeda(sal_atual)}**")
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

# --- LÓGICA DE MENU RESTRITO (SÓ VITIM E ADMINS VÊEM USUÁRIOS) ---
menu = ["📊 Dashboard", "💸 Lançar Gasto", "📥 Importar Extrato", "🎯 Metas"]

# Trava: se for o usuário 'vitim' ou se o cargo for 'admin', aparece a opção
if st.session_state.user.lower() == 'vitim' or st.session_state.role == 'admin':
    menu.append("👥 Usuários")

escolha = st.sidebar.selectbox("Menu:", menu)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---
if escolha == "📊 Dashboard":
    st.header("📊 Resumo e Fluxo")
    df = banco.buscar_gastos(st.session_state.user)
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        c1, c2 = st.columns(2)
        ano = c1.selectbox("Ano", ["Todos"] + sorted(list(df['data'].dt.year.unique()), reverse=True))
        df_f = df.copy()
        if ano != "Todos": df_f = df_f[df_f['data'].dt.year == ano]
        
        pago = df_f[df_f['status'] == 'Pago']['valor'].sum()
        pendente = df_f[df_f['status'] == 'Pendente']['valor'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Salário", f_moeda(sal_atual))
        m2.metric("Pago", f_moeda(pago))
        m3.metric("Pendente", f_moeda(pendente), delta_color="inverse")
        
        st.dataframe(df_f[['id', 'data', 'categoria', 'descricao', 'valor', 'status']], use_container_width=True)
        
        st.subheader("⚙️ Ações")
        c_st, c_xlsx = st.columns(2)
        id_st = c_st.number_input("ID para mudar status:", min_value=0, step=1)
        if c_st.button("Inverter Status (Pago/Pendente)"):
             # Lógica rápida de inversão
             atual = df_f[df_f['id'] == id_st]['status'].values[0]
             novo = "Pendente" if atual == "Pago" else "Pago"
             banco.atualizar_status_gasto(id_st, novo)
             st.rerun()
             
        output = BytesIO()
        df_f.to_excel(output, index=False)
        c_xlsx.markdown("<br>", unsafe_allow_html=True)
        c_xlsx.download_button("📥 Baixar Excel", output.getvalue(), "relatorio.xlsx")
    else:
        st.info("Lance gastos para ver o dashboard.")

elif escolha == "💸 Lançar Gasto":
    st.header("💸 Novo Gasto")
    with st.form("add"):
        c1, c2 = st.columns(2)
        d = c1.date_input("Data")
        cat = c2.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
        desc = st.text_input("Descrição")
        val = st.number_input("Valor", min_value=0.0)
        stt = st.radio("Status:", ["Pago", "Pendente"], horizontal=True)
        if st.form_submit_button("Salvar"):
            banco.salvar_gasto(st.session_state.user, d, cat, desc, val, stt)
            st.success("Salvo!")

elif escolha == "👥 Usuários":
    st.header("👥 Gestão de Usuários")
    df_u = banco.listar_usuarios()
    st.dataframe(df_u, use_container_width=True)
    
    col_a, col_b, col_c = st.columns(3)
    u_lista = df_u['usuario'].tolist()
    
    with col_a:
        u_sel = st.selectbox("Mudar Senha:", u_lista, key="u1")
        n_pw = st.text_input("Nova Senha", type="password")
        if st.button("Confirmar Senha"):
            banco.alterar_senha_usuario(u_sel, n_pw)
            st.success("Alterada!")
    with col_b:
        u_rl = st.selectbox("Mudar Cargo:", u_lista, key="u2")
        n_rl = st.radio("Nível:", ["user", "admin"])
        if st.button("Confirmar Nível"):
            if banco.alterar_nivel_usuario(u_rl, n_rl): st.rerun()
            else: st.error("Ação bloqueada para este usuário.")
    with col_c:
        u_del = st.selectbox("Remover:", [u for u in u_lista if u.lower() != 'vitim'], key="u3")
        if st.button("Confirmar Exclusão", type="primary"):
            if banco.deletar_usuario(u_del): st.rerun()

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
    v_m = st.number_input("Limite", min_value=0.0)
    if st.button("Salvar Meta"):
        banco.definir_meta(st.session_state.user, cat_m, v_m)
        st.success("Meta salva!")
