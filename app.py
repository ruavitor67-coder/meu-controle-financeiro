import streamlit as st
import pandas as pd
import banco
from datetime import date

st.set_page_config(page_title="Financeiro Pró", layout="wide")
banco.criar_tabelas()

if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔑 Login")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        nivel = banco.validar_login(u, s)
        if nivel:
            st.session_state.logado, st.session_state.user, st.session_state.nivel = True, u, nivel
            st.rerun()
        else: st.error("Erro no login")
else:
    st.sidebar.title(f"👤 {st.session_state.user}")
    sal_atual = banco.buscar_salario(st.session_state.user)
    st.sidebar.write(f"Salário: R$ {sal_atual:.2f}")
    
    with st.sidebar.expander("⚙️ Ajustar Salário"):
        n_sal = st.number_input("Valor", value=float(sal_atual))
        if st.button("Salvar Salário"):
            banco.atualizar_salario(st.session_state.user, n_sal)
            st.rerun()

    menu = ["📊 Dashboard", "💸 Lançar Gasto"]
    if st.session_state.nivel == "admin": menu.append("👥 Gerenciar Usuários")
    escolha = st.sidebar.selectbox("Menu", menu)
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if "Dashboard" in escolha:
        st.title("📊 Resumo Financeiro")
        df = banco.buscar_gastos(st.session_state.user)
        total = df['valor'].sum() if not df.empty else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Salário", f"R$ {sal_atual:.2f}")
        c2.metric("Total Gasto", f"R$ {total:.2f}")
        c3.metric("Livre", f"R$ {sal_atual - total:.2f}")

        if not df.empty:
            st.subheader("Histórico")
            for _, row in df.iterrows():
                col_i, col_d = st.columns([4, 1])
                col_i.info(f"📅 {row['data']} | {row['categoria']} | {row['descricao']} | **R$ {row['valor']:.2f}**")
                if col_d.button("🗑️", key=f"del_{row['id']}"):
                    if banco.deletar_gasto(row['id']): st.rerun()
        else: st.info("Nada lançado.")

    elif "Lançar" in escolha:
        st.title("💸 Novo Gasto")
        with st.form("gasto"):
            d = st.date_input("Data", date.today())
            cat = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Fixas", "Saúde", "Outros"])
            desc = st.text_input("Descrição")
            val = st.number_input("Valor", min_value=0.0)
            if st.form_submit_button("Salvar"):
                banco.salvar_gasto(st.session_state.user, d, cat, desc, val)
                st.success("Salvo!")
                st.rerun()

    elif "Gerenciar" in escolha:
        st.title("👥 Admin")
        with st.form("u"):
            nu, ns, nn = st.text_input("Nome"), st.text_input("Senha"), st.selectbox("Nível", ["user", "admin"])
            if st.form_submit_button("Criar"):
                if banco.adicionar_usuario(nu, ns, nn): st.success("Ok")
        st.table(banco.listar_usuarios()[['usuario', 'nivel', 'salario']])
