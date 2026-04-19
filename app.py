import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

# Função mestre para formatar moeda (converte 7000.0 em 7.000,00)
def f_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Gestão Financeira Pro", page_icon="💰", layout="wide")
banco.criar_tabelas()

if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = ""
    st.session_state.role = ""

if not st.session_state.logado:
    st.title("🔐 Acesso Restrito")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar", use_container_width=True):
        role = banco.validar_login(u, p)
        if role:
            st.session_state.logado = True
            st.session_state.user = u
            st.session_state.role = role
            st.rerun()
        else:
            st.error("Credenciais inválidas.")
    st.stop()

# --- MENU LATERAL ---
st.sidebar.title(f"👤 {st.session_state.user.upper()}")

st.sidebar.subheader("💵 Meu Salário")
sal_at = banco.buscar_salario(st.session_state.user)
# Exibimos o valor atual formatado para o usuário ver
st.sidebar.write(f"Salário Atual: **{f_moeda(sal_at)}**")

# Entrada de dados (O Streamlit usa '.' internamente, mas formatamos a saída)
n_sal = st.sidebar.number_input("Novo Salário Mensal:", min_value=0.0, value=float(sal_at), step=100.0, format="%.2f")
if st.sidebar.button("Salvar Salário"):
    banco.atualizar_salario(st.session_state.user, n_sal)
    st.sidebar.success("Salário atualizado!")
    st.rerun()

st.sidebar.divider()
menu = ["📊 Dashboard", "💸 Lançar Gasto"]
if st.session_state.role == 'admin':
    menu.append("👥 Gerenciar Usuários")
escolha = st.sidebar.selectbox("Menu:", menu)

st.sidebar.divider()
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---

if escolha == "💸 Lançar Gasto":
    st.header("💸 Novo Gasto")
    with st.form("form_gasto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        dt = col1.date_input("Data", format="DD/MM/YYYY")
        ct = col2.selectbox("Categoria", ["Alimentação", "Moradia", "Lazer", "Saúde", "Transporte", "Outros"])
        ds = st.text_input("Descrição")
        vl = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        if st.form_submit_button("Salvar"):
            if ds and vl > 0:
                banco.salvar_gasto(st.session_state.user, dt, ct, ds, vl)
                st.success(f"Gasto de {f_moeda(vl)} salvo!")
            else:
                st.warning("Preencha todos os campos.")

elif escolha == "👥 Gerenciar Usuários":
    st.header("👥 Painel Admin")
    df_u = banco.listar_usuarios()
    st.dataframe(df_u, use_container_width=True)
    
    # Seção de alteração e exclusão (Corrigido para evitar o erro de 'c' do seu log)
    c_a, c_b, c_c = st.columns(3)
    with c_a:
        u_s = st.selectbox("Trocar Senha:", df_u['usuario'].tolist(), key="s")
        n_s = st.text_input("Nova Senha", type="password")
        if st.button("Atualizar Senha"):
            banco.alterar_senha_usuario(u_s, n_s)
    with c_b:
        u_n = st.selectbox("Trocar Nível:", df_u['usuario'].tolist(), key="n")
        n_n = st.radio("Cargo:", ["user", "admin"])
        if st.button("Atualizar Nível"):
            banco.alterar_nivel_usuario(u_n, n_n)
            st.rerun()
    with c_c:
        op = [u for u in df_u['usuario'].tolist() if u.lower().strip() != 'vitim']
        u_d = st.selectbox("Deletar:", op, key="d")
        if st.button("Remover Usuário", type="primary"):
            banco.deletar_usuario(u_d)
            st.rerun()

else: # DASHBOARD
    st.header("📊 Dashboard Financeiro")
    df = banco.buscar_gastos(st.session_state.user, st.session_state.role)
    sal = banco.buscar_salario(st.session_state.user)
    
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        df['Ano'] = df['data'].dt.year.astype(str)
        
        f1, f2 = st.columns(2)
        anos = sorted(df['Ano'].unique(), reverse=True)
        a_sel = f1.selectbox("Ano", ["Todos"] + anos)
        
        df_f = df.copy()
        if a_sel != "Todos":
            df_f = df_f[df_f['Ano'] == a_sel]
            meses = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
            m_disp = sorted(df_f['data'].dt.month.unique())
            m_sel = f2.selectbox("Mês", ["Todos"] + [meses[m] for m in m_disp])
            if m_sel != "Todos":
                n_m = [k for k,v in meses.items() if v == m_sel][0]
                df_f = df_f[df_f['data'].dt.month == n_m]

        t_g = df_f['valor'].sum()
        resta = sal - t_g

        # MÉTRICAS COM FORMATAÇÃO BRASILEIRA
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Salário", f_moeda(sal))
        m2.metric("Total Gasto", f_moeda(t_g), delta_color="inverse")
        m3.metric("Saldo Atual", f_moeda(resta))

        if sal > 0:
            perc = min(t_g / sal, 1.0)
            st.progress(perc)
            st.write(f"Você consumiu **{perc*100:.1f}%** do seu salário.")
        
        st.divider()
        df_p = df_f.groupby("categoria")["valor"].sum().reset_index()
        fig = px.pie(df_p, values='valor', names='categoria', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🗑️ Apagar Lançamento")
        df_f['txt'] = df_f['id'].astype(str) + " | " + df_f['data'].dt.strftime('%d/%m/%Y') + " | " + df_f['descricao'] + " | " + df_f['valor'].apply(f_moeda)
        it = st.selectbox("Selecione:", df_f['txt'].tolist())
        if st.button("Confirmar Exclusão", type="primary"):
            banco.deletar_gasto(int(it.split("|")[0]))
            st.rerun()
    else:
        st.info(f"Seu salário é {f_moeda(sal)}. Lance gastos para ver o saldo.")
