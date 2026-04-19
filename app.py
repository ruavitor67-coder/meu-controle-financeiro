import streamlit as st
import pandas as pd
import banco  # Importa o arquivo banco.py que configuramos
from datetime import date

# Configuração da página
st.set_page_config(page_title="Controle Financeiro", layout="wide")

# Inicializa o banco de dados e as tabelas
banco.criar_tabelas()

# Inicialização do estado da sessão
if "logado" not in st.session_state:
    st.session_state.logado = False
if "user" not in st.session_state:
    st.session_state.user = None
if "nivel" not in st.session_state:
    st.session_state.nivel = None

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Login - Controle Financeiro")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        nivel = banco.validar_login(usuario, senha)
        if nivel:
            st.session_state.logado = True
            st.session_state.user = usuario
            st.session_state.nivel = nivel
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

# --- APP LOGADO ---
else:
    # Sidebar
    st.sidebar.title(f"👤 {st.session_state.user}")
    
    # Busca salário atual do banco
    salario_atual = banco.buscar_salario(st.session_state.user)
    st.sidebar.write(f"**Salário:** R$ {salario_atual:.2f}")
    
    if st.sidebar.button("Editar Salário"):
        novo_salario = st.sidebar.number_input("Novo Valor", value=float(salario_atual))
        if st.sidebar.button("Salvar Novo Salário"):
            banco.atualizar_salario(st.session_state.user, novo_salario)
            st.rerun()

    menu = ["Dashboard", "Lançar Gasto"]
    if st.session_state.nivel == "admin":
        menu.append("Gerenciar Usuários")
    
    escolha = st.sidebar.selectbox("Menu", menu)
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # --- PÁGINA: DASHBOARD ---
    if escolha == "Dashboard":
        st.title("📊 Resumo Financeiro")
        
        df = banco.buscar_gastos(st.session_state.user)
        total_gastos = df["valor"].sum() if not df.empty else 0.0
        saldo = salario_atual - total_gastos
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Orçamento", f"R$ {salario_atual:.2f}")
        col2.metric("Gasto Total", f"R$ {total_gastos:.2f}", delta=f"-R$ {total_gastos:.2f}", delta_color="inverse")
        col3.metric("Livre", f"R$ {saldo:.2f}")

        if not df.empty:
            st.subheader("Gastos por Categoria")
            import plotly.express as px
            fig = px.pie(df, values='valor', names='categoria', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Histórico de Lançamentos")
            # LISTAGEM COM BOTÃO DE APAGAR
            for _, row in df.iterrows():
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.info(f"📅 {row['data']} | {row['categoria']} | {row['descricao']} | **R$ {row['valor']:.2f}**")
                with c2:
                    if st.button("🗑️", key=f"del_{row['id']}"):
                        if banco.deletar_gasto(row['id']):
                            st.success("Apagado!")
                            st.rerun()
        else:
            st.info("Nenhum gasto cadastrado ainda.")

    # --- PÁGINA: LANÇAR GASTO ---
    elif escolha == "Lançar Gasto":
        st.title("💸 Novo Lançamento")
        with st.form("form_gasto"):
            data_gasto = st.date_input("Data", date.today())
            categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Contas Fixas", "Saúde", "Outros"])
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
            enviar = st.form_submit_button("Salvar Gasto")
            
            if enviar:
                if valor > 0:
                    banco.salvar_gasto(st.session_state.user, data_gasto, categoria, descricao, valor)
                    st.success("Gasto salvo com sucesso!")
                    st.rerun()
                else:
                    st.warning("Insira um valor maior que zero.")

    # --- PÁGINA: GERENCIAR USUÁRIOS (ADMIN) ---
    elif escolha == "Gerenciar Usuários":
        st.title("👥 Administração de Usuários")
        
        with st.form("novo_user"):
            st.write("Adicionar Novo Usuário")
            novo_u = st.text_input("Nome do Usuário")
            nova_s = st.text_input("Senha", type="password")
            novo_n = st.selectbox("Nível", ["user", "admin"])
            if st.form_submit_button("Criar"):
                if banco.adicionar_usuario(novo_u, nova_s, novo_n):
                    st.success("Criado!")
                else:
                    st.error("Erro ao criar (usuário já existe).")
        
        st.subheader("Usuários Atuais")
        lista_u = banco.listar_usuarios()
        st.table(lista_u[['usuario', 'nivel', 'salario']])
