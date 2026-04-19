import psycopg2
import pandas as pd
import streamlit as st

from passlib.hash import pbkdf2_sha256, bcrypt
from passlib.exc import InvalidHashError

# CONEXÃO
@st.cache_resource
def conectar():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"]
    )

# CRIAR TABELAS
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

        # cria admin apenas se não existir
        c.execute("SELECT 1 FROM usuarios WHERE usuario='admin'")
        if not c.fetchone():
            senha = pbkdf2_sha256.hash("admin123")
            c.execute("""
            INSERT INTO usuarios (usuario, senha, nivel)
            VALUES ('admin', %s, 'admin')
            """, (senha,))

    conn.commit()

# LOGIN COM MIGRAÇÃO AUTOMÁTICA
def validar_login(u, s):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("SELECT senha, nivel FROM usuarios WHERE usuario=%s", (u,))
        res = c.fetchone()

        if not res:
            return None

        senha_hash, nivel = res

        # 1️⃣ tenta pbkdf2 (novo padrão)
        try:
            if pbkdf2_sha256.verify(s, senha_hash):
                return nivel
        except InvalidHashError:
            pass

        # 2️⃣ tenta bcrypt antigo
        try:
            if bcrypt.verify(s[:72], senha_hash):
                # 🔄 MIGRA AUTOMATICAMENTE
                nova_hash = pbkdf2_sha256.hash(s)
                with conn.cursor() as c2:
                    c2.execute(
                        "UPDATE usuarios SET senha=%s WHERE usuario=%s",
                        (nova_hash, u)
                    )
                conn.commit()
                return nivel
        except:
            pass

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
            c.execute("INSERT INTO usuarios VALUES (%s,%s,%s,0,0)", (u, senha, n))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False

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

# FINANCEIRO
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

def buscar_salario(u):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("SELECT salario FROM usuarios WHERE usuario=%s", (u,))
        r = c.fetchone()
        return r[0] if r else 0

def atualizar_salario(u, v):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("UPDATE usuarios SET salario=%s WHERE usuario=%s", (v, u))
    conn.commit()
