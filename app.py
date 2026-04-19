import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

st.set_page_config(page_title="Meu Controle Financeiro", page_icon="💰", layout="wide")
banco.criar_tabelas()

if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = ""
    st.session_state.role = ""

if not st.session_state.logado:
    st.title("🔐 Acesso ao Sistema")
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
            st.error("Usuário ou senha inválidos.")
    st.stop()

# --- MENU LATERAL ---
st.sidebar.title(f"👤 {st.session_state.user.upper()}")
menu = ["📊 Dashboard", "💸 Lançar Gasto"]
if st.session_state.role == 'admin':
    menu.append("👥 Gerenciar Usuários")
escolha = st.sidebar.selectbox("Navegação:", menu)

st.sidebar.divider()
if st.sidebar.button("Sair", use_container_width=True):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---
if escolha == "💸 Lançar Gasto":
    st.header("💸 Registrar Novo Gasto")
    with st.form("form_gasto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        dt = col1.date_input("Data", format="DD/MM/YYYY")
        ct = col2.selectbox("Categoria", ["Alimentação", "Moradia", "Lazer", "Saúde", "Transporte", "Outros"])
        ds = st.text_input("Descrição")
        vl = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        if st.form_submit_button("Salvar Gasto", use_container_width=True):
            if ds and vl > 0:
                banco.salvar_gasto(st.session_state.user, dt, ct, ds, vl)
                st.success("Gasto salvo com sucesso!")
            else:
                st.warning("Preencha todos os campos.")

elif escolha == "👥 Gerenciar Usuários":
    st.header("👥 Gestão de Contas")
    with st.expander("➕ Criar Novo Usuário"):
        nu = st.text_input("Nome do usuário")
        np = st.text_input("Definir senha", type="password")
        nr = st.radio("Nível", ["user", "admin"], horizontal=True)
        if st.button("Cadastrar"):
            if nu and np:
                if banco.adicionar_usuario(nu, np, nr):
                    st.success(f"Usuário {nu} criado!")
                else:
                    st.error("Erro: Nome já em uso.")

else: # DASHBOARD
    st.header("📊 Resumo de Gastos")
    df = banco.buscar_gastos(st.session_state.user, st.session_state.role)
    
    if not df.empty:
        c1, c2 = st.columns(2)
        c1.metric("Total Gasto", f"R$ {df['valor'].sum():.2f}")
        c2.metric("Lançamentos", len(df))
        
        st.divider()
        df_p = df.groupby("categoria")["valor"].sum().reset_index()
        fig = px.pie(df_p, values='valor', names='categoria', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

        # SEÇÃO DE EXCLUSÃO
        with st.expander("📂 Histórico e Gerenciamento"):
            st.write("Para excluir um gasto, selecione-o abaixo:")
            # Criamos uma lista de texto para o usuário escolher qual deletar
            df['info'] = df['data'] + " - " + df['categoria'] + " - R$ " + df['valor'].map(str)
            gasto_para_deletar = st.selectbox("Selecione um gasto para remover:", df['info'])
            
            if st.button("🗑️ Excluir Gasto Selecionado", type="primary"):
                # Descobrimos o ID do gasto selecionado
                id_para_deletar = df[df['info'] == gasto_para_deletar]['id'].values[0]
                banco.deletar_gasto(id_para_deletar)
                st.success("Gasto removido!")
                st.rerun()
            
            st.divider()
            st.dataframe(df[['data', 'categoria', 'descricao', 'valor']], use_container_width=True)
    else:
        st.info("Nenhum gasto registrado.")
