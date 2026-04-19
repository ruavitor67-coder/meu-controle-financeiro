import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

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

# NOVO: Configurar Salário no Menu Lateral
st.sidebar.subheader("💵 Meu Salário")
salario_atual = banco.buscar_salario(st.session_state.user)
novo_salario = st.sidebar.number_input("Definir Salário Mensal:", min_value=0.0, value=float(salario_atual), step=100.0)
if st.sidebar.button("Salvar Salário"):
    banco.atualizar_salario(st.session_state.user, novo_salario)
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
        c1, c2 = st.columns(2)
        dt = c1.date_input("Data", format="DD/MM/YYYY")
        ct = c2.selectbox("Categoria", ["Alimentação", "Moradia", "Lazer", "Saúde", "Transporte", "Outros"])
        ds = st.text_input("O que você comprou?")
        vl = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        if st.form_submit_button("Salvar"):
            if ds and vl > 0:
                banco.salvar_gasto(st.session_state.user, dt, ct, ds, vl)
                st.success("Gasto registrado!")
            else:
                st.warning("Preencha os campos corretamente.")

elif escolha == "👥 Gerenciar Usuários":
    st.header("👥 Painel do Administrador")
    with st.expander("➕ Cadastrar Novo Usuário"):
        nu = st.text_input("Nome")
        np = st.text_input("Senha", type="password")
        nr = st.radio("Perfil", ["user", "admin"], horizontal=True)
        if st.button("Criar"):
            if nu and np:
                banco.adicionar_usuario(nu, np, nr)
                st.rerun()

    st.divider()
    df_u = banco.listar_usuarios()
    st.dataframe(df_u, use_container_width=True)

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        u_s = st.selectbox("Senha:", df_u['usuario'].tolist(), key="u_s")
        n_s = st.text_input("Nova Senha", type="password")
        if st.button("Mudar Senha"):
            banco.alterar_senha_usuario(u_s, n_s)
    with col_b:
        u_n = st.selectbox("Cargo:", df_u['usuario'].tolist(), key="u_n")
        n_n = st.radio("Nível:", ["user", "admin"])
        if st.button("Mudar Nível"):
            banco.alterar_nivel_usuario(u_n, n_n)
            st.rerun()
    with col_c:
        op_d = [u for u in df_u['usuario'].tolist() if u.lower().strip() != 'vitim']
        u_d = st.selectbox("Excluir:", op_d, key="u_d")
        if st.button("Remover", type="primary"):
            banco.deletar_usuario(u_d)
            st.rerun()

else: # DASHBOARD
    st.header("📊 Dashboard de Gastos")
    df = banco.buscar_gastos(st.session_state.user, st.session_state.role)
    salario = banco.buscar_salario(st.session_state.user)
    
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        df['Ano'] = df['data'].dt.year.astype(str)
        
        c_f1, c_f2 = st.columns(2)
        anos = sorted(df['Ano'].unique(), reverse=True)
        ano_sel = c_f1.selectbox("Ano", ["Todos"] + anos)
        
        df_filtrado = df.copy()
        if ano_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Ano'] == ano_sel]
            meses_nomes = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
            meses_disp = sorted(df_filtrado['data'].dt.month.unique())
            mes_sel = c_f2.selectbox("Mês", ["Todos"] + [meses_nomes[m] for m in meses_disp])
            if mes_sel != "Todos":
                num_m = [k for k,v in meses_nomes.items() if v == mes_sel][0]
                df_filtrado = df_filtrado[df_filtrado['data'].dt.month == num_m]

        total_gastos = df_filtrado['valor'].sum()
        saldo = salario - total_gastos

        # --- EXIBIÇÃO FINANCEIRA ---
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Salário", f"R$ {salario:.2f}")
        m2.metric("Total Gasto", f"R$ {total_gastos:.2f}", delta=f"-{total_gastos:.2f}", delta_color="inverse")
        m3.metric("Saldo Restante", f"R$ {saldo:.2f}", delta=f"{saldo:.2f}")

        # Barra de Progresso do Salário
        if salario > 0:
            percentual = min(total_gastos / salario, 1.0)
            st.write(f"**Uso do Orçamento: {percentual*100:.1f}%**")
            cor_barra = "green" if percentual < 0.7 else "orange" if percentual < 0.9 else "red"
            st.progress(percentual)
            if saldo < 0:
                st.error("⚠️ Você ultrapassou seu salário!")
        
        st.divider()
        df_p = df_filtrado.groupby("categoria")["valor"].sum().reset_index()
        fig = px.pie(df_p, values='valor', names='categoria', hole=0.4, title="Gastos por Categoria")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🗑️ Gerenciar Itens")
        df_filtrado['label'] = "ID:" + df_filtrado['id'].astype(str) + " | " + df_filtrado['data'].dt.strftime('%d/%m/%Y') + " | " + df_filtrado['descricao']
        item = st.selectbox
