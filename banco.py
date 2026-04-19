import psycopg2
import pandas as pd
import streamlit as st
from passlib.hash import pbkdf2_sha256
from datetime import datetime, timedelta
import random
import string
import smtplib
from email.mime.text import MIMEText

@st.cache_resource
def conectar():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"]
    )

# ================= TABELAS =================
def criar_tabelas():
    conn = conectar()
    with conn.cursor() as c:

        c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario TEXT PRIMARY KEY,
            email TEXT,
            senha TEXT,
            nivel TEXT,
            salario REAL DEFAULT 0,
            meta REAL DEFAULT 0,
            codigo TEXT,
            codigo_expira TIMESTAMP
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
        INSERT INTO usuarios (usuario,email,senha,nivel)
        VALUES ('admin','admin@email.com',%s,'admin')
        ON CONFLICT (usuario) DO NOTHING
        """, (senha,))

    conn.commit()

# ================= LOGIN =================
def validar_login(u, s):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("SELECT senha, nivel FROM usuarios WHERE usuario=%s", (u,))
        r = c.fetchone()
        if r and pbkdf2_sha256.verify(s, r[0]):
            return r[1]
    return None

# ================= USUÁRIOS =================
def adicionar_usuario(u, email, s, n):
    conn = conectar()
    try:
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO usuarios (usuario,email,senha,nivel) VALUES (%s,%s,%s,%s)",
                (u, email, pbkdf2_sha256.hash(s), n)
            )
        conn.commit()
        return True
    except:
        return False

def listar_usuarios():
    conn = conectar()
    return pd.read_sql("SELECT usuario,email,nivel FROM usuarios", conn)

def buscar_email(usuario):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("SELECT email FROM usuarios WHERE usuario=%s", (usuario,))
        r = c.fetchone()
        return r[0] if r else None

def redefinir_senha(usuario, nova):
    conn = conectar()
    with conn.cursor() as c:
        c.execute(
            "UPDATE usuarios SET senha=%s WHERE usuario=%s",
            (pbkdf2_sha256.hash(nova), usuario)
        )
    conn.commit()

def alterar_nivel(u, n):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("UPDATE usuarios SET nivel=%s WHERE usuario=%s", (n, u))
    conn.commit()

# ================= SALÁRIO / META =================
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

# ================= GASTOS =================
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
    return pd.read_sql(
        "SELECT * FROM gastos WHERE usuario=%s ORDER BY data DESC",
        conn,
        params=(u,)
    )

def deletar_gasto(i):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("DELETE FROM gastos WHERE id=%s", (i,))
    conn.commit()

# ================= RECUPERAÇÃO =================
def gerar_codigo():
    return ''.join(random.choices(string.digits, k=6))

def salvar_codigo(usuario, codigo):
    conn = conectar()
    expira = datetime.now() + timedelta(minutes=10)

    with conn.cursor() as c:
        c.execute("""
        UPDATE usuarios
        SET codigo=%s, codigo_expira=%s
        WHERE usuario=%s
        """, (codigo, expira, usuario))
    conn.commit()

def validar_codigo(usuario, codigo):
    conn = conectar()
    with conn.cursor() as c:
        c.execute("""
        SELECT codigo, codigo_expira FROM usuarios WHERE usuario=%s
        """, (usuario,))
        r = c.fetchone()

        if r and r[0] == codigo and datetime.now() < r[1]:
            return True
    return False

def enviar_email(destino, codigo):
    remetente = st.secrets["email"]["user"]
    senha = st.secrets["email"]["password"]

    msg = MIMEText(f"Seu código de recuperação é: {codigo}")
    msg["Subject"] = "Recuperação de senha"
    msg["From"] = remetente
    msg["To"] = destino

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)
