import streamlit as st
import pandas as pd
import plotly.express as px
import banco 
from io import BytesIO
from datetime import datetime

def f_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Gestão Financeira Ultra", page_icon="💰", layout="wide")
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
    col_v, col_b = st.sidebar.columns([2, 1])
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
if st.session_state.role == 'admin': menu.append("👥 Usuários")
escolha = st.sidebar.selectbox("Menu:", menu)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---

if escolha == "📊 Dashboard":
    st.header("📊 Fluxo de Caixa e Resumo")
    df = banco.buscar_gastos(st.session_state.user)
    
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        
        # Filtros
        c1, c2 = st.columns(2)
        ano = c1.selectbox("Ano", ["Todos"] + sorted(list(df['data'].dt.year.unique()), reverse=True))
        df_f = df.copy()
        if ano != "Todos": df_f = df_f[df_f['data'].dt.year == ano]
        
        # Métricas de Fluxo (Pago vs Pendente)
        pago = df_f[df_f['status'] == 'Pago']['valor'].sum()
        pendente = df_f[df_f['status'] == 'Pendente']['valor'].sum()
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Salário", f_moeda(sal_atual))
        m2.metric("Já Pago", f_moeda(pago), delta_color="inverse")
        m3.metric("A Pagar (Pendente)", f_moeda(pendente), delta="- " + f_moeda(pendente))
        m4.metric("Saldo Final", f_moeda(sal_atual - pago - pendente))

        # Tabela para alterar Status
        st.subheader("📝 Gerenciar Pagamentos")
        df_display = df_f[['id', 'data', 'categoria', 'descricao', 'valor', 'status']].copy()
        st.dataframe(df_display, use_container_width=True)
        
        c_up, c_del = st.columns(2)
        id_edit = c_up.number_input("ID para mudar status:", min_value=0, step=1)
        novo_st = c_up.selectbox("Novo Status:", ["Pago", "Pendente"])
        if c_up.button("Atualizar Status"):
            banco.atualizar_status_gasto(id_edit, novo_st)
            st.rerun()

        # Gráfico e Excel
        st.plotly_chart(px.pie(df_f, values='valor', names='categoria', title="Gastos por Categoria"))
        output = BytesIO()
        df_f.to_excel(output, index=False)
        st.download_button("📥 Baixar Relatório", output.getvalue(), "relatorio.xlsx")
    else:
        st.info("Sem dados.")

elif escolha == "💸 Lançar Gasto":
    st.header("💸 Novo Lançamento")
    df_antigo = banco.buscar_gastos(st.session_state.user)
    
    with st.form("gasto"):
        c1, c2 = st.columns(2)
        data = c1.date_input("Data")
        # IA: Sugestão baseada na última descrição igual
        desc = st.text_input("Descrição (Ex: Aluguel, Mercado...)")
        
        cat_sugerida = "Outros"
        if desc and not df_antigo.empty:
            match = df_antigo[df_antigo['descricao'].str.contains(desc, case=False, na=False)]
            if not match.empty:
                cat_sugerida = match.iloc[-1]['categoria']
        
        cat = c2.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"], 
                           index=["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"].index(cat_sugerida))
        
        valor = st.number_input("Valor", min_value=0.0)
        status = st.radio("Status:", ["Pago", "Pendente"], horizontal=True)
        
        if st.form_submit_button("Salvar"):
            banco.salvar_gasto(st.session_state.user, data, cat, desc, valor, status)
            st.success("Lançado!")

elif escolha == "📥 Importar Extrato":
    st.header("📥 Importar Excel/CSV")
    st.write("Envie um arquivo com as colunas: **data, categoria, descricao, valor**")
    arquivo = st.file_uploader("Escolha o arquivo", type=['csv', 'xlsx'])
    
    if arquivo:
        try:
            if arquivo.name.endswith('.csv'): df_imp = pd.read_csv(arquivo)
            else: df_imp = pd.read_excel(arquivo)
            
            st.write("Prévia dos dados:")
            st.dataframe(df_imp.head())
            
            if st.button("Confirmar Importação"):
                for _, row in df_imp.iterrows():
                    banco.salvar_gasto(st.session_state.user, row['data'], row['categoria'], row['descricao'], row['valor'])
                st.success("Tudo importado com sucesso!")
        except Exception as e:
            st.error(f"Erro no formato do arquivo: {e}")

elif escolha == "🎯 Metas":
    st.header("🎯 Metas")
    cat_m = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
    val_m = st.number_input("Limite Mensal", min_value=0.0)
    if st.button("Definir Meta"):
        banco.definir_meta(st.session_state.user, cat_m, val_m)
        st.success("Meta salva!")

elif escolha == "👥 Usuários":
    st.header("👥 Gestão de Usuários")
    df_u = banco.listar_usuarios()
    st.dataframe(df_u)
    c1, c2, c3 = st.columns(3)
    u_sel = c1.selectbox("Usuário:", df_u['usuario'].tolist())
    if c1.button("Excluir Usuário"):
        if banco.deletar_usuario(u_sel): st.rerun()
    n_p = c2.text_input("Nova Senha", type="password")
    if c2.button("Mudar Senha"):
        banco.alterar_senha_usuario(u_sel, n_p)
        st.success("Senha alterada!")
