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
    st.session_state.logado, st.session_state.user, st.session_state.editando_salario = False, "", False

# --- LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        role = banco.validar_login(u, p)
        if role:
            st.session_state.logado, st.session_state.user = True, u
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
    n_sal = st.sidebar.number_input("Valor:", value=float(sal_atual))
    if st.sidebar.button("Salvar"):
        banco.atualizar_salario(st.session_state.user, n_sal)
        st.session_state.editando_salario = False
        st.rerun()

st.sidebar.divider()
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "💸 Gastos", "🎯 Metas"])
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- DASHBOARD COM FILTROS E EXPORTAÇÃO ---
if menu == "📊 Dashboard":
    st.header("📊 Painel de Controle")
    df = banco.buscar_gastos(st.session_state.user)
    
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        
        # 1. FILTROS POR PERÍODO
        c_ano, c_mes, c_exp = st.columns([1, 1, 1])
        anos = sorted(df['data'].dt.year.unique(), reverse=True)
        ano_sel = c_ano.selectbox("Ano", ["Todos"] + list(anos))
        
        df_f = df.copy()
        if ano_sel != "Todos":
            df_f = df_f[df_f['data'].dt.year == ano_sel]
            meses = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
            m_disp = sorted(df_f['data'].dt.month.unique())
            mes_sel = c_mes.selectbox("Mês", ["Todos"] + [meses[m] for m in m_disp])
            if mes_sel != "Todos":
                m_num = [k for k,v in meses.items() if v == mes_sel][0]
                df_f = df_f[df_f['data'].dt.month == m_num]

        # 3. EXPORTAÇÃO PARA EXCEL
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_f.drop(columns=['usuario']).to_excel(writer, index=False, sheet_name='Gastos')
        c_exp.markdown("<br>", unsafe_allow_html=True) # Alinhamento
        c_exp.download_button("📥 Baixar Excel", output.getvalue(), "meus_gastos.xlsx")

        # MÉTRICAS
        total = df_f['valor'].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Salário", f_moeda(sal_atual))
        m2.metric("Total Gasto", f_moeda(total), delta_color="inverse")
        m3.metric("Saldo", f_moeda(sal_atual - total))

        # 2. ALERTA DE METAS
        st.subheader("⚠️ Status das Metas")
        df_metas = banco.buscar_metas(st.session_state.user)
        df_cat = df_f.groupby("categoria")["valor"].sum().reset_index()
        
        for index, row in df_metas.iterrows():
            gasto_cat = df_cat[df_cat['categoria'] == row['categoria']]['valor'].sum()
            perc = min(gasto_cat / row['limite'], 1.0) if row['limite'] > 0 else 0
            cor = "red" if gasto_cat > row['limite'] else "green"
            st.write(f"**{row['categoria']}**: {f_moeda(gasto_cat)} de {f_moeda(row['limite'])}")
            st.progress(perc)
            if gasto_cat > row['limite']:
                st.error(f"🚨 Limite de {row['categoria']} ultrapassado!")

        st.divider()
        st.plotly_chart(px.pie(df_f, values='valor', names='categoria', hole=0.4), use_container_width=True)
    else:
        st.info("Lance gastos para ativar o dashboard.")

elif menu == "💸 Gastos":
    st.header("💸 Lançar Gasto")
    with st.form("gasto"):
        d = st.date_input("Data")
        c = st.selectbox("Categoria", ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Outros"])
        ds = st.text_input("Descrição")
        v = st.number_input("Valor", min_value=0.0, format="%.2f")
        if st.form_submit_button("Salvar"):
            banco.salvar_gasto(st.session_state.user, d, c, ds, v)
            st.success("Gasto salvo!")
            st.rerun()

elif menu == "🎯 Metas":
    st.header("🎯 Definir Limites Mensais")
    with st.form("meta"):
        cat = st.selectbox("Categoria", ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Outros"])
        lim = st.number_input("Limite Máximo (R$)", min_value=0.0)
        if st.form_submit_button("Definir Meta"):
            banco.definir_meta(st.session_state.user, cat, lim)
            st.success(f"Meta para {cat} definida!")
