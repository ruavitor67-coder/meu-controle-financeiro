import streamlit as st
import pandas as pd
import plotly.express as px
import banco 
from io import BytesIO

def f_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Gestão Financeira", page_icon="💰", layout="wide")
banco.criar_tabelas()

# Inicializa estados de sessão
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

# --- SIDEBAR (INTERFACE DO SALÁRIO CORRIGIDA) ---
st.sidebar.title(f"👤 {st.session_state.user.upper()}")
sal_atual = banco.buscar_salario(st.session_state.user)

st.sidebar.subheader("💵 Configurar Salário")

if not st.session_state.editando_salario:
    # Interface Limpa: Mostra valor e botão Alterar na mesma linha
    col_v, col_b = st.sidebar.columns([1.5, 1])
    col_v.write(f"Atual: **{f_moeda(sal_atual)}**")
    if col_b.button("Alterar"):
        st.session_state.editando_salario = True
        st.rerun()
else:
    # Interface de Edição: Só aparece ao clicar em Alterar
    n_sal = st.sidebar.number_input("Novo Salário:", value=float(sal_atual), step=100.0)
    c1, c2 = st.sidebar.columns(2)
    if c1.button("Salvar"):
        banco.atualizar_salario(st.session_state.user, n_sal)
        st.session_state.editando_salario = False
        st.success("Salário salvo!")
        st.rerun()
    if c2.button("Cancelar"):
        st.session_state.editando_salario = False
        st.rerun()

st.sidebar.divider()
# --- RESTO DO MENU E DASHBOARD ---
menu = ["📊 Dashboard", "💸 Lançar Gasto", "🎯 Metas"]
if st.session_state.role == 'admin': menu.append("👥 Usuários")
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
        # Filtros e Gráficos (Mantidos como estavam)
        c1, c2 = st.columns(2)
        ano = c1.selectbox("Ano", ["Todos"] + list(df['data'].dt.year.unique()))
        df_f = df.copy()
        if ano != "Todos": df_f = df_f[df_f['data'].dt.year == ano]
        
        st.metric("Total Gasto", f_moeda(df_f['valor'].sum()))
        st.plotly_chart(px.pie(df_f, values='valor', names='categoria', hole=0.4))
        
        # Botão de Exportação Excel (Mantido)
        output = BytesIO()
        df_f.to_excel(output, index=False)
        st.download_button("📥 Baixar Relatório Excel", output.getvalue(), "gastos.xlsx")
    else:
        st.info("Nenhum gasto encontrado para este período.")

elif escolha == "💸 Lançar Gasto":
    st.header("💸 Novo Gasto")
    with st.form("add"):
        d = st.date_input("Data")
        c = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
        ds = st.text_input("Descrição")
        v = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("Salvar"):
            banco.salvar_gasto(st.session_state.user, d, c, ds, v)
            st.success("Gasto salvo!")

elif escolha == "👥 Usuários":
    st.header("👥 Gestão de Usuários")
    df_u = banco.listar_usuarios()
    st.dataframe(df_u, use_container_width=True)
    
    col_a, col_b, col_c = st.columns(3)
    u_lista = df_u['usuario'].tolist()
    with col_a:
        u_sel = st.selectbox("Mudar Senha:", u_lista, key="pw")
        n_pw = st.text_input("Nova Senha", type="password")
        if st.button("Confirmar Senha"):
            banco.alterar_senha_usuario(u_sel, n_pw)
            st.success("Senha alterada!")
    with col_b:
        u_rl = st.selectbox("Mudar Nível:", u_lista, key="rl")
        n_rl = st.radio("Nível:", ["user", "admin"])
        if st.button("Confirmar Cargo"):
            banco.alterar_nivel_usuario(u_rl, n_rl)
            st.rerun()
    with col_c:
        u_del = st.selectbox("Deletar:", [u for u in u_lista if u.lower() != 'vitim'], key="del")
        if st.button("Excluir", type="primary"):
            banco.deletar_usuario(u_del)
            st.rerun()

elif escolha == "🎯 Metas":
    st.header("🎯 Metas")
    cat_m = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
    v_m = st.number_input("Limite", min_value=0.0)
    if st.button("Salvar Meta"):
        banco.definir_meta(st.session_state.user, cat_m, v_m)
        st.success("Meta definida!")
