import streamlit as st
import pandas as pd
import banco
import plotly.express as px
from datetime import date

st.set_page_config(page_title="Controle Financeiro", layout="wide")
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
        else: st.error("Erro no login")
else:
    # --- SIDEBAR (CONFORME IMAGE_5EB8D1) ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    sal_atual = banco.buscar_salario(st.session_state.user)
    st.sidebar.write(f"**Salário:** R$ {sal_atual:.2f}")
    
    if st.sidebar.button("Editar Salário"):
        st.session_state.edit_sal = True
    
    if st.session_state.get("edit_sal"):
        n_sal = st.sidebar.number_input("Novo Valor", value=float(sal_atual))
        if st.sidebar.button("Salvar Salário"):
            banco.atualizar_salario(st.session_state.user, n_sal)
            st.session_state.edit_sal = False
            st.rerun()

    menu = ["📊 Dashboard", "💸 Lançar Gasto"]
    if st.session_state.nivel == "admin": 
        menu.append("👥 Gerenciamento de Usuários")
    
    escolha = st.sidebar.selectbox("Módulo", menu)
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # --- DASHBOARD (CONFORME IMAGE_5E544C) ---
    if "Dashboard" in escolha:
        st.title("📊 Resumo Financeiro")
        df = banco.buscar_gastos(st.session_state.user)
        total = df['valor'].sum() if not df.empty else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Orçamento", f"R$ {sal_atual:.2f}")
        c2.metric("Gasto Total", f"R$ {total:.2f}", delta=f"-R$ {total:.2f}", delta_color="inverse")
        c3.metric("Livre", f"R$ {sal_atual - total:.2f}")

        if not df.empty:
            fig = px.pie(df, values='valor', names='categoria', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 Meus Lançamentos")
            for _, row in df.iterrows():
                col_i, col_d = st.columns([5, 1])
                col_i.info(f"📅 {row['data']} | {row['categoria']} | {row['descricao']} | **R$ {row['valor']:.2f}**")
                if col_d.button("🗑️", key=f"del_{row['id']}"):
                    if banco.deletar_gasto(row['id']):
                        st.rerun()
        else:
            st.info("Nada lançado.")

    # --- ADMIN (CONFORME IMAGE_5ECFB4) ---
    elif "Gerenciamento" in escolha:
        st.title("👥 Gerenciamento de Usuários")
        with st.form("novo_u"):
            nu, ns, nn = st.text_input("Nome"), st.text_input("Senha"), st.selectbox("Nível", ["user", "admin"])
            if st.form_submit_button("Criar Conta"):
                if banco.adicionar_usuario(nu, ns, nn): st.success("Criado!")
                else: st.error("Erro")
        
        st.table(banco.listar_usuarios()[['usuario', 'nivel', 'salario']])

    # --- LANÇAR GASTO ---
    elif "Lançar" in escolha:
        st.title("💸 Novo Lançamento")
        with st.form("add"):
            d, cat, desc, val = st.date_input("Data"), st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Fixas", "Outros"]), st.text_input("Descrição"), st.number_input("Valor")
            if st.form_submit_button("Salvar"):
                banco.salvar_gasto(st.session_state.user, d, cat, desc, val)
                st.rerun()
