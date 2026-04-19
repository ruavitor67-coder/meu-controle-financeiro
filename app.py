import streamlit as st
import pandas as pd
import plotly.express as px
import banco 

# ✨ Função para formatar números para exibição (ex: 7.000,00)
def f_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Gestão Financeira", page_icon="💰", layout="wide")
banco.criar_tabelas()

# Inicialização de estados de sessão
if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.user = ""
    st.session_state.role = ""

if 'editando_salario' not in st.session_state:
    st.session_state.editando_salario = False

# --- LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Login")
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

# --- SIDEBAR ---
st.sidebar.title(f"👤 {st.session_state.user.upper()}")

# --- MELHORIA: Gestão Dinâmica do Salário ---
st.sidebar.subheader("💵 Salário Mensal")
sal_atual = banco.buscar_salario(st.session_state.user)

if not st.session_state.editando_salario:
    # Mostra o valor formatado e o botão de alterar ao lado
    col_v, col_b = st.sidebar.columns([1.5, 1])
    col_v.write(f"**{f_moeda(sal_atual)}**")
    if col_b.button("Alterar"):
        st.session_state.editando_salario = True
        st.rerun()
else:
    # Mostra o campo de entrada e os botões de Salvar/Cancelar
    n_sal = st.sidebar.number_input("Definir Valor:", min_value=0.0, value=float(sal_atual), step=100.0, format="%.2f")
    c1, c2 = st.sidebar.columns(2)
    if c1.button("Salvar"):
        banco.atualizar_salario(st.session_state.user, n_sal)
        st.session_state.editando_salario = False
        st.sidebar.success("Salvo!")
        st.rerun()
    if c2.button("Cancelar"):
        st.session_state.editando_salario = False
        st.rerun()

st.sidebar.divider()
menu = ["📊 Dashboard", "💸 Lançar Gasto"]
if st.session_state.role == 'admin':
    menu.append("👥 Usuários")
escolha = st.sidebar.selectbox("Ir para:", menu)

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# --- TELAS ---

if escolha == "💸 Lançar Gasto":
    st.header("💸 Novo Gasto")
    with st.form("add_gasto", clear_on_submit=True):
        c1, c2 = st.columns(2)
        data = c1.date_input("Data")
        cat = c2.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Saúde", "Lazer", "Outros"])
        desc = st.text_input("Descrição")
        # Melhoria: Campo de valor formatado com 2 casas decimais
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        if st.form_submit_button("Salvar"):
            if desc and valor > 0:
                banco.salvar_gasto(st.session_state.user, data, cat, desc, valor)
                st.success(f"Gasto de {f_moeda(valor)} registrado!")
            else:
                st.warning("Preencha todos os campos.")

elif escolha == "👥 Usuários":
    st.header("👥 Gestão de Usuários")
    df_u = banco.listar_usuarios()
    st.dataframe(df_u, use_container_width=True)
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        u_sel = st.selectbox("Mudar Senha:", df_u['usuario'].tolist(), key="u_pw")
        n_pw = st.text_input("Nova Senha", type="password")
        if st.button("Confirmar Senha"):
            banco.alterar_senha_usuario(u_sel, n_pw)
            st.success("Senha alterada!")
    with col_b:
        u_cargo = st.selectbox("Mudar Cargo:", df_u['usuario'].tolist(), key="u_rl")
        n_rl = st.radio("Nível:", ["user", "admin"])
        if st.button("Confirmar Cargo"):
            banco.alterar_nivel_usuario(u_cargo, n_rl)
            st.rerun()
    with col_c:
        deletar_lista = [u for u in df_u['usuario'].tolist() if u.lower() != 'vitim']
        u_del = st.selectbox("Remover:", deletar_lista, key="u_del")
        if st.button("Confirmar Exclusão", type="primary"):
            banco.deletar_usuario(u_del)
            st.rerun()

else: # DASHBOARD
    st.header("📊 Resumo Financeiro")
    # Nota: Removi o parâmetro extra caso o seu banco.py aceite apenas usuario
    df = banco.buscar_gastos(st.session_state.user, st.session_state.role)
    sal = banco.buscar_salario(st.session_state.user)
    
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        total_gasto = df['valor'].sum()
        saldo_restante = sal - total_gasto

        # Métricas Formatadas no padrão brasileiro
        m1, m2, m3 = st.columns(3)
        m1.metric("Salário Atual", f_moeda(sal))
        m2.metric("Total Gasto", f_moeda(total_gasto), delta_color="inverse")
        m3.metric("Saldo Restante", f_moeda(saldo_restante))

        st.divider()
        df_p = df.groupby("categoria")["valor"].sum().reset_index()
        fig = px.pie(df_p, values='valor', names='categoria', hole=0.4, title="Gastos por Categoria")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🗑️ Remover Registro")
        # Exibe os itens da lista também com o valor formatado
        df['item'] = df['id'].astype(str) + " | " + df['data'].dt.strftime('%d/%m/%Y') + " | " + df['descricao'] + " | " + df['valor'].apply(f_moeda)
        it_del = st.selectbox("Selecione para excluir:", df['item'].tolist())
        if st.button("Excluir Gasto", type="primary"):
            banco.deletar_gasto(int(it_del.split("|")[0]))
            st.rerun()
    else:
        st.info(f"Salário: {f_moeda(sal)}. Lance gastos para ver o resumo.")
