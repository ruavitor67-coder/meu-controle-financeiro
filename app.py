import streamlit as st
import pandas as pd
import banco
import plotly.express as px
from datetime import date

st.set_page_config(page_title="Gestão Financeira Pró", layout="wide")
banco.criar_tabelas()

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Acesso ao Sistema")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        nivel = banco.validar_login(u, s)
        if nivel:
            st.session_state.logado, st.session_state.user, st.session_state.nivel = True, u, nivel
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
else:
    # --- BARRA LATERAL COMPLETA ---
    st.sidebar.title(f"👤 {st.session_state.user}")
    salario = banco.buscar_salario(st.session_state.user)
    st.sidebar.write(f"**Salário Atual:** R$ {salario:.2f}")
    
    with st.sidebar.expander("⚙️ Configurações"):
        novo_sal = st.number_input("Ajustar Salário", value=float(salario))
        if st.button("Atualizar Salário"):
            banco.atualizar_salario(st.session_state.user, novo_sal)
            st.rerun()

    menu = ["📊 Dashboard", "💸 Novo Lançamento"]
    if st.session_state.nivel == "admin":
        menu.append("👥 Administração")
    
    escolha = st.sidebar.selectbox("Navegação", menu)
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # --- DASHBOARD ---
    if escolha == "📊 Dashboard":
        st.title("📊 Resumo Financeiro")
        df = banco.buscar_gastos(st.session_state.user)
        total_gasto = df['valor'].sum() if not df.empty else 0
        saldo = salario - total_gasto
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Orçamento", f"R$ {salario:.2f}")
        c2.metric("Gasto Total", f"R$ {total_gasto:.2f}", delta=f"-R$ {total_gasto:.2f}", delta_color="inverse")
        c3.metric("Livre", f"R$ {saldo:.2f}")

        if not df.empty:
            st.subheader("Análise por Categoria")
            fig = px.pie(df, values='valor', names='categoria', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 Meus Lançamentos")
            # Tabela Estilizada com Ações
            for _, row in df.iterrows():
                col_i, col_s, col_d = st.columns([4, 1, 0.5])
                col_i.info(f"📅 {row['data']} | {row['categoria']} | {row['descricao']} | **R$ {row['valor']:.2f}**")
                col_s.write(f"Status: {row['status']}")
                if col_d.button("🗑️", key=f"del_{row['id']}"):
                    if banco.deletar_gasto(row['id']):
                        st.rerun()
        else:
            st.warning("Você ainda não tem gastos cadastrados.")

    # --- LANÇAMENTO ---
    elif escolha == "💸 Novo Lançamento":
        st.title("💸 Cadastrar Despesa")
        with st.form("novo_gasto"):
            d = st.date_input("Data", date.today())
            cat = st.selectbox("Categoria", ["Alimentação", "Moradia", "Lazer", "Transporte", "Saúde", "Fixas", "Outros"])
            desc = st.text_input("Descrição do Gasto")
            val = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            st.form_submit_button("Salvar")
            if val > 0:
                banco.salvar_gasto(st.session_state.user, d, cat, desc, val)
                st.success("Lançamento realizado!")
                st.rerun()

    # --- ADMIN ---
    elif escolha == "👥 Administração":
        st.title("👥 Gerenciamento de Usuários")
        with st.form("cad_user"):
            st.subheader("Novo Usuário")
            nu, ns, nn = st.text_input("Nome de Usuário"), st.text_input("Senha", type="password"), st.selectbox("Perfil", ["user", "admin"])
            if st.form_submit_button("Criar Conta"):
                if banco.adicionar_usuario(nu, ns, nn): st.success("Criado!")
                else: st.error("Erro ao criar.")
        
        st.subheader("Lista de Acessos")
        users_df = banco.listar_usuarios()
        st.dataframe(users_df, use_container_width=True)
