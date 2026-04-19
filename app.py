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
                st.warning("Preencha os campos corretamente.")

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
        # --- PREPARAÇÃO DAS DATAS ---
        df['data'] = pd.to_datetime(df['data'])
        df['Ano'] = df['data'].dt.year.astype(str)
        df['Mês'] = df['data'].dt.month_name() # Nome do mês
        df['Dia'] = df['data'].dt.strftime('%d/%m/%Y')
        
        # --- LINHA DE FILTROS ---
        st.subheader("🔍 Filtros")
        col_f1, col_f2, col_f3 = st.columns(3)
        
        # Filtro de Ano
        anos = sorted(df['Ano'].unique(), reverse=True)
        ano_sel = col_f1.selectbox("Filtrar por Ano:", ["Todos"] + anos)
        
        # Filtro de Mês
        if ano_sel != "Todos":
            df_mes = df[df['Ano'] == ano_sel]
            meses = sorted(df_mes['data'].dt.month.unique())
            # Converte números para nomes de meses amigáveis
            nomes_meses = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho',
                           7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
            meses_nomes = [nomes_meses[m] for m in meses]
            mes_sel = col_f2.selectbox("Filtrar por Mês:", ["Todos"] + meses_nomes)
        else:
            mes_sel = col_f2.selectbox("Filtrar por Mês:", ["Selecione um ano"], disabled=True)

        # Filtro de Dia
        if mes_sel != "Todos" and ano_sel != "Todos":
            # Inverte o dicionário para pegar o número do mês de volta
            num_mes = [k for k, v in nomes_meses.items() if v == mes_sel][0]
            df_dia = df[(df['Ano'] == ano_sel) & (df['data'].dt.month == num_mes)]
            dias = sorted(df_dia['Dia'].unique(), reverse=True)
            dia_sel = col_f3.selectbox("Filtrar por Dia:", ["Todos"] + dias)
        else:
            dia_sel = col_f3.selectbox("Filtrar por Dia:", ["Selecione um mês"], disabled=True)

        # --- APLICAÇÃO DOS FILTROS NO DATAFRAME ---
        df_filtrado = df.copy()
        if ano_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Ano'] == ano_sel]
        if mes_sel != "Todos" and ano_sel != "Todos":
            num_mes = [k for k, v in nomes_meses.items() if v == mes_sel][0]
            df_filtrado = df_filtrado[df_filtrado['data'].dt.month == num_mes]
        if dia_sel != "Todos" and ano_sel != "Todos" and mes_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Dia'] == dia_sel]

        # --- EXIBIÇÃO ---
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Total no Período", f"R$ {df_filtrado['valor'].sum():.2f}")
        c2.metric("Lançamentos", len(df_filtrado))
        
        st.divider()
        
        # Gráfico dinâmico
        if not df_filtrado.empty:
            df_p = df_filtrado.groupby("categoria")["valor"].sum().reset_index()
            fig = px.pie(df_p, values='valor', names='categoria', hole=0.4, title="Divisão por Categoria")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("🗑️ Gerenciar Lançamentos")
            df_filtrado['item_selecao'] = "ID:" + df_filtrado['id'].astype(str) + " | " + df_filtrado['Dia'] + " | " + df_filtrado['descricao']
            opcoes_excluir = df_filtrado['item_selecao'].tolist()
            selecionado = st.selectbox("Selecione para apagar:", opcoes_excluir)
            
            if st.button("Confirmar Exclusão", type="primary"):
                id_real = int(selecionado.split("|")[0].replace("ID:", "").strip())
                banco.deletar_gasto(id_real)
                st.success("Removido!")
                st.rerun()
        else:
            st.warning("Nenhum gasto encontrado para os filtros selecionados.")

    else:
        st.info("Nenhum gasto registrado ainda.")
