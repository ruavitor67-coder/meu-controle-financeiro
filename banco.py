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
            c.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, senha TEXT, nivel TEXT, salario REAL DEFAULT 0)")
            c.execute("CREATE TABLE IF NOT EXISTS gastos (id SERIAL PRIMARY KEY, usuario TEXT, data TEXT, categoria TEXT, valor REAL)")
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
