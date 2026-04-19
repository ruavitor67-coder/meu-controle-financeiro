import streamlit as st
import pandas as pd
import banco
import plotly.express as px
from datetime import date

# Configuração inicial
st.set_page_config(page_title="Controle Financeiro Profissional", layout="wide")
banco.criar_tabelas()

# Controle de sessão
if "logado" not in st.session_state:
    st.session_state.logado = False

# --- TELA DE ACESSO ---
if not st.session_state.logado:
    st.title("🔐 Login do Sistema")
    col_l, col_r = st.columns(2)
    with col_l:
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            nivel = banco.validar_login(u, s)
            if nivel:
                st.session_state.logado = True
                st.session_state.user = u
                st.session_state.nivel = nivel
                st.rerun()
            else:
                st.error("Credenciais inválidas.")

# --- SISTEMA LOGADO ---
else:
    # Sidebar Restaurada
    st.sidebar.title(f"👤 Usuário: {st.session_state.user}")
    salario = banco.buscar_salario(st.session_state.user)
    st.sidebar.write(f"💼 **Salário:** R$ {salario:.2f}")
    
    with st.sidebar.expander("🛠️ Ajustes"):
        novo_sal = st.number_input("Novo Salário", value=float(salario), step=100.0)
        if st.button("Salvar Salário"):
            banco.atualizar_salario(st.session_state.user, novo_sal)
            st.rerun()

    menu = ["📊 Dashboard", "💸 Adicionar Gasto"]
    if st.session_state.nivel == "admin":
        menu.append("👥 Gestão de Usuários")
    
    escolha = st.sidebar.selectbox("Navegar para:", menu)
    
    if st.sidebar.button("Encerrar Sessão"):
        st.session_state.logado = False
        st.rerun()

    # --- PÁGINA: DASHBOARD ---
    if escolha == "📊 Dashboard":
        st.title("📊 Resumo Financeiro")
        df = banco.buscar_gastos(st.session_state.user)
        total_gasto = df['valor'].sum() if not df.empty else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Orçamento", f"R$ {salario:.2f}")
        c2.metric("Gasto Total", f"R$ {total_gasto:.2f}", delta=f"-R$ {total_gasto:.2f}", delta_color="inverse")
        c3.metric("Disponível", f"R$ {salario - total_gasto:.2f}")

        if not df.empty:
            st.subheader("Distribuição de Gastos")
            fig = px.pie(df, values='valor', names='categoria', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 Detalhamento de Lançamentos")
            # Lista com botão de exclusão
            for _, row in df.iterrows():
                with st.container():
                    col_info, col_status, col_acao = st.columns([4, 1, 0.5])
                    col_info.info(f"📅 {row['data']} | **{row['categoria']}** | {row['descricao']} | **R$ {row['valor']:.2f}**")
                    col_status.write(f"📌 {row['status']}")
                    if col_acao.button("🗑️", key=f"btn_del_{row['id']}"):
                        if banco.deletar_gasto(row['id']):
                            st.rerun()
        else:
            st.info("Nenhum lançamento encontrado.")

    # --- PÁGINA: NOVO GASTO ---
    elif escolha == "💸 Adicionar Gasto":
        st.title("💸 Novo Lançamento")
        with st.form("form_novo_gasto"):
            d = st.date_input("Data da Despesa", date.today())
            cat = st.selectbox("Categoria", ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Fixas", "Outros"])
            desc = st.text_input("Descrição (Ex: Supermercado)")
            val = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            status = st.selectbox("Status", ["Pago", "Pendente"])
            
            if st.form_submit_button("Lançar no Sistema"):
                if val > 0:
                    banco.salvar_gasto(st.session_state.user, d, cat, desc, val, status)
                    st.success("Gasto registrado!")
                    st.rerun()
                else:
                    st.error("O valor deve ser maior que zero.")

    # --- PÁGINA: ADMIN ---
    elif escolha == "👥 Gestão de Usuários":
        st.title("👥 Painel Administrativo")
        with st.form("cad_user"):
            st.write("### Criar Novo Usuário")
            nu, ns, nn = st.text_input("Nome de Usuário"), st.text_input("Senha", type="password"), st.selectbox("Perfil", ["user", "admin"])
            if st.form_submit_button("Cadastrar"):
                if banco.adicionar_usuario(nu, ns, nn): st.success("Usuário criado!")
                else: st.error("Erro: Nome de usuário já existe.")
        
        st.write("### Usuários Cadastrados")
        users_df = banco.listar_usuarios()
        st.dataframe(users_df, use_container_width=True)
