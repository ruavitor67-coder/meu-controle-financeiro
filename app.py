import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

# ✨ Função para formatar moeda no padrão brasileiro
def f_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Gestão Financeira Pro", page_icon="💰", layout="wide")
banco.criar_tabelas()

# --- Lógica de Sessão ---
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = ""
if 'editando_salario' not in st.session_state:
    st.session_state.editando_salario = False

# (Insira aqui sua lógica de Login para definir st.session_state.logado)

if st.session_state.logado:
    # --- SIDEBAR ---
    st.sidebar.title(f"👤 {st.session_state.user.upper()}")
    st.sidebar.subheader("💵 Configurar Salário")
    
    sal_atual = banco.buscar_salario(st.session_state.user)

    if not st.session_state.editando_salario:
        # 👁️ Modo de Exibição: Valor e Botão Lado a Lado
        col_txt, col_btn = st.sidebar.columns([1.5, 1])
        col_txt.write(f"Atual: **{f_moeda(sal_atual)}**")
        if col_btn.button("Alterar"):
            st.session_state.editando_salario = True
            st.rerun()
    else:
        # ✍️ Modo de Edição: Campo e Botão de Salvar
        n_sal = st.sidebar.number_input("Novo Salário:", min_value=0.0, value=float(sal_atual), format="%.2f")
        if st.sidebar.button("Confirmar Salário"):
            banco.atualizar_salario(st.session_state.user, n_sal)
            st.session_state.editando_salario = False
            st.rerun()

    st.sidebar.divider()
    menu = st.sidebar.selectbox("Menu:", ["📊 Dashboard", "💸 Lançar Gasto"])

    # --- TELAS ---
    if menu == "📊 Dashboard":
        st.header("📊 Dashboard Financeiro")
        df = banco.buscar_gastos(st.session_state.user)
        total_gasto = df['valor'].sum() if not df.empty else 0
        saldo = sal_atual - total_gasto

        m1, m2, m3 = st.columns(3)
        m1.metric("Salário", f_moeda(sal_atual))
        m2.metric("Total Gasto", f_moeda(total_gasto), delta_color="inverse")
        m3.metric("Saldo Restante", f_moeda(saldo))

        if not df.empty:
            fig = px.pie(df, values='valor', names='categoria', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

    elif menu == "💸 Lançar Gasto":
        st.header("💸 Novo Gasto")
        with st.form("gasto_form"):
            desc = st.text_input("Descrição")
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            cat = st.selectbox("Categoria", ["Alimentação", "Lazer", "Saúde", "Outros"])
            if st.form_submit_button("Salvar"):
                banco.salvar_gasto(st.session_state.user, "2023-10-27", cat, desc, valor)
                st.success("Gasto salvo!")
                st.rerun()
