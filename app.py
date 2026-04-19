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
escolha = st.sidebar.selectbox("Menu:", menu)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---

if escolha == "📊 Dashboard":
    st.header("📊 Painel de Controle e Metas")
    df = banco.buscar_gastos(st.session_state.user)
    df_metas = banco.buscar_metas(st.session_state.user)
    
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        total_gasto = df['valor'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Salário", f_moeda(sal_atual))
        m2.metric("Total Gasto", f_moeda(total_gasto))
        m3.metric("Disponível", f_moeda(sal_atual - total_gasto))
        
        st.divider()
        
        # --- MELHORIA: ACOMPANHAMENTO DE METAS ---
        st.subheader("🎯 Progresso das Metas Mensais")
        if not df_metas.empty:
            for _, m in df_metas.iterrows():
                cat = m['categoria']
                lim = m['limite']
                gasto_cat = df[df['categoria'] == cat]['valor'].sum()
                
                # Cálculo de porcentagem para a barra
                progresso = min(gasto_cat / lim, 1.0) if lim > 0 else 0
                
                # Layout da Meta
                c_txt, c_bar = st.columns([1, 3])
                c_txt.write(f"**{cat}**")
                
                # Cor da barra baseada no limite
                if progresso < 0.8:
                    c_bar.progress(progresso)
                elif progresso < 1.0:
                    c_bar.progress(progresso)
                    st.warning(f"Atenção: Meta de {cat} quase atingida!")
                else:
                    c_bar.progress(1.0)
                    st.error(f"⚠️ Meta de {cat} ESTOURADA!")
                
                st.caption(f"Gasto: {f_moeda(gasto_cat)} | Limite: {f_moeda(lim)}")
        else:
            st.info("Nenhuma meta definida ainda.")

        st.divider()
        st.plotly_chart(px.pie(df, values='valor', names='categoria', hole=0.4, title="Distribuição de Gastos"))
        st.subheader("📝 Últimos Lançamentos")
        st.dataframe(df.sort_values(by='data', ascending=False), use_container_width=True)
    else:
        st.info("Lance gastos para visualizar o dashboard.")

elif escolha == "💸 Lançar Gasto":
    st.header("💸 Novo Lançamento")
    with st.form("add"):
        c1, c2 = st.columns(2)
        d = c1.date_input("Data")
        cat = c2.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
        ds = st.text_input("Descrição")
        v = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("Salvar Gasto"):
            banco.salvar_gasto(st.session_state.user, d, cat, ds, v)
            st.success("Lançado com sucesso!")

elif escolha == "👥 Usuários":
    st.header("👥 Gestão de Usuários")
    df_u = banco.listar_usuarios()
    st.dataframe(df_u, use_container_width=True)
    col_a, col_b, col_c = st.columns(3)
    u_lista = df_u['usuario'].tolist()
    with col_a:
        u_pw = st.selectbox("Usuário:", u_lista, key="p1")
        n_pw = st.text_input("Senha:", type="password", key="p2")
        if st.button("Trocar Senha"):
            banco.alterar_senha_usuario(u_pw, n_pw)
            st.success("Pronto!")
    with col_b:
        u_rl = st.selectbox("Usuário:", u_lista, key="r1")
        n_rl = st.radio("Cargo:", ["user", "admin"])
        if st.button("Trocar Cargo"):
            if banco.alterar_nivel_usuario(u_rl, n_rl): st.rerun()
    with col_c:
        u_del = st.selectbox("Excluir:", [u for u in u_lista if u.lower() != 'vitim'], key="d1")
        if st.button("Confirmar Exclusão", type="primary"):
            if banco.deletar_usuario(u_del): st.rerun()

elif escolha == "🎯 Metas":
    st.header("🎯 Definir Metas")
    cat_m = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
    lim_m = st.number_input("Limite Máximo (R$)", min_value=0.0)
    if st.button("Salvar Meta"):
        banco.definir_meta(st.session_state.user, cat_m, lim_m)
        st.success(f"Meta de {cat_m} salva!")

elif escolha == "📥 Importar Extrato":
    st.header("📥 Importação")
    st.info("Suba um arquivo Excel/CSV com colunas: data, categoria, descricao, valor")
    arq = st.file_uploader("Arquivo:", type=['csv', 'xlsx'])
    if arq:
        st.success("Arquivo pronto para processamento!")
