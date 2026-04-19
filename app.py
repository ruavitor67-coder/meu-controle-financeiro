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
                st.warning("Preencha a descrição e o valor.")

elif escolha == "👥 Gerenciar Usuários":
    st.header("👥 Painel do Administrador")
    
    with st.expander("➕ Cadastrar Novo Usuário"):
        nu = st.text_input("Nome de Usuário")
        np = st.text_input("Senha Temporária", type="password")
        nr = st.radio("Perfil", ["user", "admin"], horizontal=True)
        if st.button("Confirmar Cadastro"):
            if nu and np:
                if banco.adicionar_usuario(nu, np, nr):
                    st.success(f"Usuário {nu} criado!")
                    st.rerun()
                else:
                    st.error("Usuário já existe.")

    st.divider()
    st.subheader("📋 Lista de Acessos")
    df_u = banco.listar_usuarios()
    st.dataframe(df_u, use_container_width=True)

    st.divider()
    # TRÊS COLUNAS: Senha, Nível e Exclusão
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.subheader("🔑 Senha")
        u_senha = st.selectbox("Usuário:", df_u['usuario'].tolist(), key="u_s")
        n_senha = st.text_input("Nova Senha", type="password")
        if st.button("Mudar Senha"):
            if n_senha:
                banco.alterar_senha_usuario(u_senha, n_senha)
                st.success("Senha atualizada!")

    with col_b:
        st.subheader("🛡️ Cargo")
        u_nivel = st.selectbox("Usuário:", df_u['usuario'].tolist(), key="u_n")
        n_nivel = st.radio("Novo Nível:", ["user", "admin"], key="rad_n")
        if st.button("Alterar Nível"):
            if u_nivel.lower() == 'vitim':
                st.error("O mestre não pode ser rebaixado.")
            else:
                banco.alterar_nivel_usuario(u_nivel, n_nivel)
                st.success(f"{u_nivel} agora é {n_nivel}!")
                st.rerun()

    with col_c:
        st.subheader("🗑️ Remover")
        opcoes_del = [u for u in df_u['usuario'].tolist() if u.lower().strip() != 'vitim']
        if opcoes_del:
            u_del = st.selectbox("Usuário:", opcoes_del, key="u_d")
            if st.button("Excluir", type="primary"):
                if u_del == st.session_state.user:
                    st.error("Saia para se excluir.")
                else:
                    banco.deletar_usuario(u_del)
                    st.balloons()
                    st.rerun()
        else:
            st.info("Apenas você no sistema.")

else: # DASHBOARD
    st.header("📊 Resumo Financeiro")
    df = banco.buscar_gastos(st.session_state.user, st.session_state.role)
    
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        df['Ano'] = df['data'].dt.year.astype(str)
        
        col_f1, col_f2 = st.columns(2)
        anos = sorted(df['Ano'].unique(), reverse=True)
        ano_sel = col_f1.selectbox("Ano", ["Todos"] + anos)
        
        meses_nomes = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
        
        df_filtrado = df.copy()
        if ano_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Ano'] == ano_sel]
            meses_disp = sorted(df_filtrado['data'].dt.month.unique())
            mes_sel = col_f2.selectbox("Mês", ["Todos"] + [meses_nomes[m] for m in meses_disp])
            if mes_sel != "Todos":
                num_mes = [k for k, v in meses_nomes.items() if v == mes_sel][0]
                df_filtrado = df_filtrado[df_filtrado['data'].dt.month == num_mes]
        else:
            col_f2.info("Selecione o ano.")

        c1, c2 = st.columns(2)
        c1.metric("Gasto Total", f"R$ {df_filtrado['valor'].sum():.2f}")
        c2.metric("Itens", len(df_filtrado))
        
        st.divider()
        df_p = df_filtrado.groupby("categoria")["valor"].sum().reset_index()
        fig = px.pie(df_p, values='valor', names='categoria', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🗑️ Excluir Lançamento")
        df_filtrado['label'] = "ID:" + df_filtrado['id'].astype(str) + " | " + df_filtrado['data'].dt.strftime('%d/%m/%Y') + " | " + df_filtrado['descricao']
        item = st.selectbox("Escolha o item:", df_filtrado['label'].tolist())
        if st.button("Confirmar Exclusão", type="primary"):
            id_id = int(item.split("|")[0].replace("ID:", "").strip())
            banco.deletar_gasto(id_id)
            st.rerun()
    else:
        st.info("Lance gastos para ativar o painel.")
