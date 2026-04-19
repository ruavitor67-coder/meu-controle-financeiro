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
            nivel TEXT,
            salario REAL DEFAULT 0,
            meta REAL DEFAULT 0
        )
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
        r = c.fetchone()
        if r and pbkdf2_sha256.verify(s, r[0]):
            return r[1]
    return None

def redefinir_senha(usuario, nova):
    conn = conectar()
    with conn.cursor() as c:
        c.execute(
            "UPDATE usuarios SET senha=%s WHERE usuario=%s",
            (pbkdf2_sha256.hash(nova), usuario)
        )
    conn.commit()

# USUÁRIOS
def listar_usuarios():
    conn = conectar()
    return pd.read_sql("SELECT usuario, nivel FROM usuarios", conn)

def adicionar_usuario(u, s, n):
    conn = conectar()
    try:
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO usuarios VALUES (%s,%s,%s,0,0)",
                (u, pbkdf2_sha256.hash(s), n)
            )
        conn.commit()
        return True
    except:
        return False

def alterar_senha(u, s):
    redefinir_senha(u, s)

def alterar_nivel(u, n):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("UPDATE usuarios SET nivel=%s WHERE usuario=%s", (n, u))
    conn.commit()

# SALÁRIO / META
def buscar_salario(u):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("SELECT salario FROM usuarios WHERE usuario=%s", (u,))
        return c.fetchone()[0]

def atualizar_salario(u, v):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("UPDATE usuarios SET salario=%s WHERE usuario=%s", (v, u))
    conn.commit()

def buscar_meta(u):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("SELECT meta FROM usuarios WHERE usuario=%s", (u,))
        return c.fetchone()[0]

def atualizar_meta(u, v):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("UPDATE usuarios SET meta=%s WHERE usuario=%s", (v, u))
    conn.commit()

# GASTOS
def salvar_gasto(u, d, cat, desc, v, status):
    conn = conectar()
    with conn.cursor() as c:
        c.execute(
            "INSERT INTO gastos (usuario,data,categoria,descricao,valor,status) VALUES (%s,%s,%s,%s,%s,%s)",
            (u, d, cat, desc, v, status)
        )
    conn.commit()

def buscar_gastos(u):
    conn = conectar()
    return pd.read_sql("SELECT * FROM gastos WHERE usuario=%s ORDER BY data DESC", conn, params=(u,))

def deletar_gasto(i):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("DELETE FROM gastos WHERE id=%s", (i,))
    conn.commit()
