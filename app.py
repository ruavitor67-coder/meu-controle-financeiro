import streamlit as st
import pandas as pd
import banco
import plotly.express as px
from datetime import date

st.set_page_config(page_title="Gestão Financeira", layout="wide")
banco.criar_tabelas()

if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        nivel = banco.validar_login(u, s)
        if nivel:
            st.session_state.logado, st.session_state.user, st.session_state.nivel = True, u, nivel
            st.rerun()
        else: st.error("Login inválido.")
else:
    # --- BARRA LATERAL (OPÇÕES ANTIGAS DE VOLTA) ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    sal_atual = banco.buscar_salario(st.session_state.user)
    st.sidebar.metric("Seu Salário", f"R$ {sal_atual:.2f}")
    
    with st.sidebar.expander("📝 Editar Salário"):
        n_sal = st.number_input("Novo Valor", value=float(sal_atual))
        if st.button("Salvar Salário"):
            banco.atualizar_salario(st.session_state.user, n_sal)
            st.rerun()

    menu = ["📊 Dashboard", "💸 Lançar Gasto"]
    if st.session_state.nivel == "admin": menu.append("👥 Admin")
    escolha = st.sidebar.selectbox("Módulo", menu)
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # --- DASHBOARD ---
    if "Dashboard" in escolha:
        st.title("📊 Resumo Financeiro")
        df = banco.buscar_gastos(st.session_state.user)
        total = df['valor'].sum() if not df.empty else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Orçamento", f"R$ {sal_atual:.2f}")
        col2.metric("Gasto Total", f"R$ {total:.2f}", delta=f"-R$ {total:.2f}", delta_color="inverse")
        col3.metric("Livre", f"R$ {sal_atual - total:.2f}")

        if not df.empty:
            st.subheader("Gastos por Categoria")
            fig = px.pie(df, values='valor', names='categoria', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 Meus Lançamentos")
            for _, row in df.iterrows():
                c1, c2 = st.columns([5, 1])
                c1.info(f"📅 {row['data']} | {row['categoria']} | {row['descricao']} | **R$ {row['valor']:.2f}**")
                if c2.button("🗑️", key=f"del_{row['id']}"):
                    if banco.deletar_gasto(row['id']): st.rerun()
        else: st.info("Nenhum dado para exibir.")

    # --- LANÇAR GASTO ---
    elif "Lançar" in escolha:
        st.title("💸 Novo Lançamento")
        with st.form("add_gasto"):
            d = st.date_input("Data", date.today())
            cat = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Fixas", "Saúde", "Outros"])
            desc = st.text_input("Descrição")
            val = st.number_input("Valor", min_value=0.0)
            if st.form_submit_button("Confirmar Lançamento"):
                banco.salvar_gasto(st.session_state.user, d, cat, desc, val)
                st.success("Lançado!")
                st.rerun()

    # --- ADMIN ---
    elif "Admin" in escolha:
        st.title("👥 Gerenciar Usuários")
        with st.form("novo_user"):
            nu, ns, nn = st.text_input("Nome"), st.text_input("Senha"), st.selectbox("Nível", ["user", "admin"])
            if st.form_submit_button("Criar Usuário"):
                if banco.adicionar_usuario(nu, ns, nn): st.success("Usuário criado!")
                else: st.error("Erro ao criar.")
        
        st.subheader("Usuários Atuais")
        users = banco.listar_usuarios()
        st.table(users[['usuario', 'nivel', 'salario']])
