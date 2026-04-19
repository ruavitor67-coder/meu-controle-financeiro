import psycopg2
import pandas as pd
import streamlit as st
from passlib.hash import pbkdf2_sha256

@st.cache_resource
def conectar():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"]
    )

def criar_tabelas():
    conn = conectar()
    with conn.cursor() as c:

        c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario TEXT PRIMARY KEY,
            senha TEXT,
            nivel TEXT
        )
        """)

        c.execute("""
        ALTER TABLE usuarios
        ADD COLUMN IF NOT EXISTS salario REAL DEFAULT 0
        """)

        c.execute("""
        ALTER TABLE usuarios
        ADD COLUMN IF NOT EXISTS meta REAL DEFAULT 0
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id SERIAL PRIMARY KEY,
            usuario TEXT,
            data DATE,
            categoria TEXT,
            descricao TEXT,
            valor REAL,
            status TEXT
        )
        """)

        senha = pbkdf2_sha256.hash("admin123")

        c.execute("""
        INSERT INTO usuarios (usuario, senha, nivel)
        VALUES ('admin', %s, 'admin')
        ON CONFLICT (usuario) DO NOTHING
        """, (senha,))

    conn.commit()

# LOGIN
def validar_login(u, s):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("SELECT senha, nivel FROM usuarios WHERE usuario=%s", (u,))
        res = c.fetchone()

        if not res:
            return None

        senha_hash, nivel = res

        try:
            if pbkdf2_sha256.verify(s, senha_hash):
                return nivel
        except:
            return None

    return None

# USUÁRIOS
def listar_usuarios():
    conn = conectar()
    return pd.read_sql("SELECT usuario, nivel, salario, meta FROM usuarios", conn)

def adicionar_usuario(u, s, n):
    conn = conectar()
    try:
        senha = pbkdf2_sha256.hash(s)
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO usuarios (usuario, senha, nivel) VALUES (%s,%s,%s)",
                (u, senha, n)
            )
        conn.commit()
        return True
    except:
        return False

# ADMIN FUNÇÕES
def atualizar_salario_admin(usuario, valor):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("UPDATE usuarios SET salario=%s WHERE usuario=%s", (valor, usuario))
    conn.commit()

def alterar_senha(usuario, nova_senha):
    conn = conectar()
    senha_hash = pbkdf2_sha256.hash(nova_senha)
    with conn.cursor() as c:
        c.execute("UPDATE usuarios SET senha=%s WHERE usuario=%s", (senha_hash, usuario))
    conn.commit()

def alterar_nivel(usuario, nivel):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("UPDATE usuarios SET nivel=%s WHERE usuario=%s", (nivel, usuario))
    conn.commit()

# META
def buscar_meta(u):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("SELECT meta FROM usuarios WHERE usuario=%s", (u,))
        r = c.fetchone()
        return r[0] if r else 0

def atualizar_meta(u, v):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("UPDATE usuarios SET meta=%s WHERE usuario=%s", (v, u))
    conn.commit()

# SALÁRIO
def buscar_salario(u):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("SELECT salario FROM usuarios WHERE usuario=%s", (u,))
        r = c.fetchone()
        return r[0] if r else 0

# GASTOS
def salvar_gasto(u, d, cat, desc, v, status):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("""
        INSERT INTO gastos (usuario,data,categoria,descricao,valor,status)
        VALUES (%s,%s,%s,%s,%s,%s)
        """, (u, d, cat, desc, v, status))
    conn.commit()

def buscar_gastos(u):
    conn = conectar()
    return pd.read_sql(
        "SELECT * FROM gastos WHERE usuario=%s ORDER BY data DESC",
        conn,
        params=(u,)
    )

def deletar_gasto(id):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("DELETE FROM gastos WHERE id=%s", (id,))
    conn.commit()
