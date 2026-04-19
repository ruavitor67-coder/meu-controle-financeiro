import psycopg2
import hashlib
import pandas as pd
import streamlit as st

# Conexão com o Supabase
def conectar():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"]
    )

# Cria as tabelas automaticamente se não existirem
def criar_tabelas():
    with conectar() as conn:
        with conn.cursor() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS usuarios 
                         (usuario TEXT PRIMARY KEY, senha TEXT, nivel TEXT, salario REAL DEFAULT 0)""")
            c.execute("""CREATE TABLE IF NOT EXISTS gastos 
                         (id SERIAL PRIMARY KEY, usuario TEXT, data TEXT, 
                          categoria TEXT, descricao TEXT, valor REAL, status TEXT DEFAULT 'Pago')""")
            
            # Garante que o Admin exista
            h = hashlib.sha256("admin123".encode()).hexdigest()
            c.execute("INSERT INTO usuarios (usuario, senha, nivel) VALUES ('admin', %s, 'admin') ON CONFLICT DO NOTHING", (h,))
        conn.commit()

def validar_login(usuario, senha):
    try:
        with conectar() as conn:
            with conn.cursor() as c:
                h = hashlib.sha256(senha.encode()).hexdigest()
                c.execute("SELECT nivel FROM usuarios WHERE usuario=%s AND senha=%s", (usuario, h))
                res = c.fetchone()
                return res[0] if res else None
    except: return None

def buscar_salario(usuario):
    with conectar() as conn:
        with conn.cursor() as c:
            c.execute("SELECT salario FROM usuarios WHERE usuario=%s", (usuario,))
            res = c.fetchone()
            return res[0] if res else 0

def atualizar_salario(usuario, valor):
    with conectar() as conn:
        with conn.cursor() as c:
            c.execute("UPDATE usuarios SET salario=%s WHERE usuario=%s", (valor, usuario))
        conn.commit()

def salvar_gasto(usuario, data, categoria, descricao, valor, status='Pago'):
    with conectar() as conn:
        with conn.cursor() as c:
            c.execute("INSERT INTO gastos (usuario, data, categoria, descricao, valor, status) VALUES (%s, %s, %s, %s, %s, %s)",
                      (usuario, str(data), categoria, descricao, valor, status))
        conn.commit()

def buscar_gastos(usuario):
    with conectar() as conn:
        return pd.read_sql("SELECT data, categoria, descricao, valor, status FROM gastos WHERE usuario=%s", conn, params=(usuario,))

def listar_usuarios():
    with conectar() as conn:
        return pd.read_sql("SELECT usuario, nivel, salario FROM usuarios", conn)

def adicionar_usuario(nome, senha, nivel):
    try:
        with conectar() as conn:
            with conn.cursor() as c:
                h = hashlib.sha256(senha.encode()).hexdigest()
                c.execute("INSERT INTO usuarios (usuario, senha, nivel, salario) VALUES (%s, %s, %s, 0)", (nome, h, nivel))
            conn.commit()
            return True
    except: return False

def deletar_usuario(nome):
    try:
        with conectar() as conn:
            with conn.cursor() as c:
                c.execute("DELETE FROM gastos WHERE usuario=%s", (nome,))
                c.execute("DELETE FROM usuarios WHERE usuario=%s", (nome,))
            conn.commit()
            return True
    except: return False
