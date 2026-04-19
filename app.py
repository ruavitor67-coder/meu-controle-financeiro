import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

# Configuração Base
st.set_page_config(page_title="Controle Financeiro", page_icon="💰", layout="wide")
banco.criar_tabelas()

if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = ""
    st.session_state.role = ""

# --- TELA DE LOGIN ---
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
                st.warning("Preencha todos os campos corretamente.")

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
                    st.error("Erro: Nome já existe.")

else: # DASHBOARD
    st.header("📊 Resumo de Gastos")
    df = banco.buscar_gastos(st.session_state.user, st.session_state.role)
    
    if not df.empty:
        c1, c2 = st.columns(2)
        c1.metric("Total Gasto", f"R$ {df['valor'].sum():.2f}")
        c2.metric("Lançamentos", len(df))
        
        st.divider()
        
        # Gráfico
        df_p = df.groupby("categoria")["valor"].sum().reset_index()
        fig = px.pie(df_p, values='valor', names='categoria', hole=0.4, title="Divisão por Categoria")
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("🗑️ Gerenciar Lançamentos")
        
        # Criamos uma lista formatada para o seletor
        # O segredo: adicionamos o ID no texto da seleção para o Python não se confundir
        df['item_selecao'] = "ID:" + df['id'].astype(str) + " | " + df['data'] + " | " + df['descricao'] + " (R$ " + df['valor'].astype(str) + ")"
        
        opcoes_excluir = df['item_selecao'].tolist()
        selecionado = st.selectbox("Selecione o gasto que deseja apagar:", opcoes_excluir)
        
        if st.button("Confirmar Exclusão", type="primary"):
            # Extraímos o ID real a partir do texto selecionado
            id_real = int(selecionado.split("|")[0].replace("ID:", "").strip())
            
            banco.deletar_gasto(id_real)
            st.success("Lançamento removido!")
            st.rerun()

        with st.expander("📂 Ver Tabela Completa"):
            st.dataframe(df[['data', 'categoria', 'descricao', 'valor']], use_container_width=True)
    else:
        st.info("Nenhum dado encontrado. Comece a lançar seus gastos!")
