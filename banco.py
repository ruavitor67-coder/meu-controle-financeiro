import psycopg2
import hashlib
import pandas as pd
import streamlit as st
from psycopg2.extras import RealDictCursor

# Função de conexão com tratamento de erro para evitar quedas no refresh
def conectar():
    try:
        return psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            database=st.secrets["postgres"]["database"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            port=st.secrets["postgres"]["port"],
            connect_timeout=10
        )
    except Exception as e:
        st.error(f"Erro crítico de conexão: {e}")
        return None

def criar_tabelas():
    conn = conectar()
    if conn:
        with conn.cursor() as c:
            # Tabela de usuários com todas as colunas originais
            c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
                usuario TEXT PRIMARY KEY, 
                senha TEXT, 
                nivel TEXT, 
                salario REAL DEFAULT 0
            )""")
            
            # Tabela de gastos completa com SERIAL ID e STATUS
            c.execute("""CREATE TABLE IF NOT EXISTS gastos (
                id SERIAL PRIMARY KEY, 
                usuario TEXT, 
                data TEXT, 
                categoria TEXT, 
                descricao TEXT, 
                valor REAL, 
                status TEXT DEFAULT 'Pago'
            )""")
            
            # Criar Admin inicial se a tabela estiver vazia
            h = hashlib.sha256("admin123".encode()).hexdigest()
            c.execute("INSERT INTO usuarios (usuario, senha, nivel) VALUES ('admin', %s, 'admin') ON CONFLICT DO NOTHING", (h,))
        conn.commit()
        conn.close()

# --- ÁREA DE SEGURANÇA E LOGIN ---
def validar_login(u, s):
    conn = conectar()
    if not conn: return None
    try:
        with conn.cursor() as c:
            h = hashlib.sha256(s.encode()).hexdigest()
            c.execute("SELECT nivel FROM usuarios WHERE usuario=%s AND senha=%s", (u, h))
            res = c.fetchone()
            return res[0] if res else None
    finally:
        conn.close()

# --- GESTÃO DE USUÁRIOS (ADMIN) ---
def listar_usuarios():
    conn = conectar()
    if not conn: return pd.DataFrame()
    try:
        return pd.read_sql("SELECT usuario, nivel, salario FROM usuarios ORDER BY usuario ASC", conn)
    finally:
        conn.close()

def adicionar_usuario(u, s, n):
    conn = conectar()
    if not conn: return False
    try:
        with conn.cursor() as c:
            h = hashlib.sha256(s.encode()).hexdigest()
            c.execute("INSERT INTO usuarios (usuario, senha, nivel, salario) VALUES (%s, %s, %s, 0)", (u, h, n))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def deletar_usuario(u):
    conn = conectar()
    if conn:
        with conn.cursor() as c:
            c.execute("DELETE FROM gastos WHERE usuario=%s", (u,))
            c.execute("DELETE FROM usuarios WHERE usuario=%s", (u,))
        conn.commit()
        conn.close()

# --- GESTÃO FINANCEIRA ---
def buscar_salario(u):
    conn = conectar()
    if not conn: return 0.0
    try:
        with conn.cursor() as c:
            c.execute("SELECT salario FROM usuarios WHERE usuario=%s", (u,))
            res = c.fetchone()
            return res[0] if res else 0.0
    finally:
        conn.close()

def atualizar_salario(u, v):
    conn = conectar()
    if conn:
        with conn.cursor() as c:
            c.execute("UPDATE usuarios SET salario=%s WHERE usuario=%s", (v, u))
        conn.commit()
        conn.close()

def salvar_gasto(u, d, cat, desc, v, status='Pago'):
    conn = conectar()
    if conn:
        with conn.cursor() as c:
            c.execute("""INSERT INTO gastos (usuario, data, categoria, descricao, valor, status) 
                         VALUES (%s, %s, %s, %s, %s, %s)""", (u, str(d), cat, desc, v, status))
        conn.commit()
        conn.close()

def buscar_gastos(u):
    conn = conectar()
    if not conn: return pd.DataFrame()
    try:
        # Puxa todas as colunas necessárias para o Dashboard
        query = "SELECT id, data, categoria, descricao, valor, status FROM gastos WHERE usuario=%s ORDER BY data DESC"
        return pd.read_sql(query, conn, params=(u,))
    finally:
        conn.close()

def deletar_gasto(id_gasto):
    conn = conectar()
    if conn:
        try:
            with conn.cursor() as c:
                c.execute("DELETE FROM gastos WHERE id = %s", (id_gasto,))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()
    return False

def atualizar_status_gasto(id_gasto, novo_status):
    conn = conectar()
    if conn:
        with conn.cursor() as c:
            c.execute("UPDATE gastos SET status=%s WHERE id=%s", (novo_status, id_gasto))
        conn.commit()
        conn.close()
