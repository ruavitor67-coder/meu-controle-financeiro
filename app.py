import streamlit as st
import pandas as pd
import banco
import plotly.express as px
from datetime import date

st.set_page_config(page_title="Gestão Financeira Completa", layout="wide")
banco.criar_tabelas()

if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")
    u, s = st.text_input("Usuário"), st.text_input("Senha", type="password")
    if st.button("Entrar"):
        nivel = banco.validar_login(u, s)
        if nivel:
            st.session_state.logado, st.session_state.user, st.session_state.nivel = True, u, nivel
            st.rerun()
        else: st.error("Login Inválido.")
else:
    # --- SIDEBAR COMPLETA ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    sal_atual = banco.buscar_salario(st.session_state.user)
    st.sidebar.metric("Orçamento Atual", f"R$ {sal_atual:.2f}")
    
    with st.sidebar.expander("⚙️ Editar Salário"):
        n_sal = st.number_input("Novo Valor", value=float(sal_atual))
        if st.button("Salvar Salário"):
            banco.atualizar_salario(st.session_state.user, n_sal)
            st.rerun()

    menu = ["📊 Dashboard", "💸 Lançar Gasto"]
    if st.session_state.nivel == "admin": menu.append("👥 Admin Usuários")
    escolha = st.sidebar.selectbox("Módulo", menu)
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # --- DASHBOARD COM GRÁFICO ---
    if "Dashboard" in escolha:
        st.title("📊 Painel de Controle")
        df = banco.buscar_gastos(st.session_state.user)
        total = df['valor'].sum() if not df.empty else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Saldo Inicial", f"R$ {sal_atual:.2f}")
        c2.metric("Total Gasto", f"R$ {total:.2f}", delta=f"-R$ {total:.2f}", delta_color="inverse")
        c3.metric("Livre para Uso", f"R$ {sal_atual - total:.2f}")

        if not df.empty:
            st.subheader("Distribuição por Categoria")
            fig = px.pie(df, values='valor', names='categoria', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 Histórico com Opção de Excluir")
            for _, row in df.iterrows():
                col_info, col_btn = st.columns([5, 1])
                col_info.info(f"📅 {row['data']} | {row['categoria']} | {row['descricao']} | **R$ {row['valor']:.2f}**")
                if col_btn.button("🗑️", key=f"del_{row['id']}"):
                    if banco.deletar_gasto(row['id']):
                        st.success("Excluído!")
                        st.rerun()
        else:
            st.info("Nenhum lançamento encontrado para este usuário.")

    # --- LANÇAMENTOS ---
    elif "Lançar" in escolha:
        st.title("💸 Novo Lançamento")
        with st.form("form_gasto"):
            d = st.date_input("Data", date.today())
            cat = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Fixas", "Saúde", "Outros"])
            desc = st.text_input("Descrição")
            val = st.number_input("Valor (R$)", min_value=0.0)
            if st.form_submit_button("Confirmar Gasto"):
                banco.salvar_gasto(st.session_state.user, d, cat, desc, val)
                st.success("Gasto salvo!")
                st.rerun()

    # --- ADMIN ---
    elif "Admin" in escolha:
        st.title("👥 Gerenciamento de Usuários")
        with st.form("add_u"):
            nu, ns, nn = st.text_input("Nome"), st.text_input("Senha"), st.selectbox("Nível", ["user", "admin"])
            if st.form_submit_button("Criar Conta"):
                if banco.adicionar_usuario(nu, ns, nn): st.success("Usuário criado!")
                else: st.error("Erro (talvez já exista).")
        st.table(banco.listar_usuarios()[['usuario', 'nivel', 'salario']])
