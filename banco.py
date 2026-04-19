import psycopg2
import hashlib
import pandas as pd
import streamlit as st

def conectar():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"]
    )

def criar_tabelas():
    with conectar() as conn:
        with conn.cursor() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS usuarios 
                         (usuario TEXT PRIMARY KEY, senha TEXT, nivel TEXT, salario REAL DEFAULT 0)""")
            c.execute("""CREATE TABLE IF NOT EXISTS gastos 
                         (id SERIAL PRIMARY KEY, usuario TEXT, data TEXT, 
                          categoria TEXT, descricao TEXT, valor REAL, status TEXT DEFAULT 'Pago')""")
            h = hashlib.sha256("admin123".encode()).hexdigest()
            c.execute("INSERT INTO usuarios (usuario, senha, nivel) VALUES ('admin', %s, 'admin') ON CONFLICT DO NOTHING", (h,))
        conn.commit()

def validar_login(u, s):
    try:
        with conectar() as conn:
            with conn.cursor() as c:
                h = hashlib.sha256(s.encode()).hexdigest()
                c.execute("SELECT nivel FROM usuarios WHERE usuario=%s AND senha=%s", (u, h))
                res = c.fetchone()
                return res[0] if res else None
    except: return None

def buscar_salario(u):
    with conectar() as conn:
        with conn.cursor() as c:
            c.execute("SELECT salario FROM usuarios WHERE usuario=%s", (u,))
            res = c.fetchone()
            return res[0] if res else 0

def atualizar_salario(u, v):
    with conectar() as conn:
        with conn.cursor() as c:
            c.execute("UPDATE usuarios SET salario=%s WHERE usuario=%s", (v, u))
        conn.commit()

def salvar_gasto(u, d, cat, desc, v, status='Pago'):
    with conectar() as conn:
        with conn.cursor() as c:
            c.execute("INSERT INTO gastos (usuario, data, categoria, descricao, valor, status) VALUES (%s, %s, %s, %s, %s, %s)", 
                      (u, str(d), cat, desc, v, status))
        conn.commit()

def buscar_gastos(u):
    with conectar() as conn:
        return pd.read_sql("SELECT id, data, categoria, descricao, valor, status FROM gastos WHERE usuario=%s ORDER BY data DESC", conn, params=(u,))

def deletar_gasto(id_gasto):
    try:
        with conectar() as conn:
            with conn.cursor() as c:
                c.execute("DELETE FROM gastos WHERE id = %s", (id_gasto,))
            conn.commit()
            return True
    except: return False

def listar_usuarios():
    with conectar() as conn:
        return pd.read_sql("SELECT usuario, nivel, salario FROM usuarios", conn)

def adicionar_usuario(u, s, n):
    try:
        with conectar() as conn:
            with conn.cursor() as c:
                h = hashlib.sha256(s.encode()).hexdigest()
                c.execute("INSERT INTO usuarios (usuario, senha, nivel, salario) VALUES (%s, %s, %s, 0)", (u, h, n))
            conn.commit()
            return True
    except: return False

def deletar_usuario(u):
    try:
        with conectar() as conn:
            with conn.cursor() as c:
                c.execute("DELETE FROM gastos WHERE usuario=%s", (u,))
                c.execute("DELETE FROM usuarios WHERE usuario=%s", (u,))
            conn.commit()
            return True
    except: return False
