import psycopg2
import streamlit as st
import time
from passlib.hash import pbkdf2_sha256


# ================= CONEXÃO BLINDADA =================
def conectar():
    for tentativa in range(5):
        try:
            conn = psycopg2.connect(
                host=st.secrets["DB_HOST"],
                database=st.secrets["DB_NAME"],
                user=st.secrets["DB_USER"],
                password=st.secrets["DB_PASS"],
                port=st.secrets["DB_PORT"],
                sslmode="require",
                connect_timeout=10
            )
            return conn

        except Exception as e:
            print(f"Tentativa {tentativa+1} falhou:", e)
            time.sleep(2)

    raise Exception("❌ Não conseguiu conectar ao banco")


# ================= CRIAR TABELAS =================
def criar_tabelas():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY,
        email TEXT,
        senha TEXT,
        nivel TEXT,
        salario NUMERIC DEFAULT 0,
        meta NUMERIC DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS gastos (
        id SERIAL PRIMARY KEY,
        usuario TEXT,
        data DATE,
        categoria TEXT,
        descricao TEXT,
        valor NUMERIC,
        status TEXT
    )
    """)

    # admin padrão
    senha = pbkdf2_sha256.hash("admin123")

    c.execute("""
    INSERT INTO usuarios (usuario, email, senha, nivel)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (usuario) DO NOTHING
    """, ("admin", "admin@email.com", senha, "admin"))

    conn.commit()
    conn.close()


# ================= LOGIN =================
def validar_login(usuario, senha):
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT senha, nivel FROM usuarios WHERE usuario=%s", (usuario,))
    r = c.fetchone()

    conn.close()

    if r and pbkdf2_sha256.verify(senha, r[0]):
        return r[1]

    return None


# ================= USUÁRIOS =================
def criar_usuario(u, email, s, nivel):
    conn = conectar()
    c = conn.cursor()

    senha = pbkdf2_sha256.hash(s)

    c.execute("""
    INSERT INTO usuarios VALUES (%s,%s,%s,%s,0,0)
    ON CONFLICT DO NOTHING
    """, (u, email, senha, nivel))

    conn.commit()
    conn.close()


def listar_usuarios():
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT usuario, nivel, salario, meta FROM usuarios")
    dados = c.fetchall()

    conn.close()
    return dados


def excluir_usuario(u):
    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM usuarios WHERE usuario=%s", (u,))
    conn.commit()
    conn.close()


# ================= SALARIO / META =================
def atualizar_salario(u, v):
    conn = conectar()
    c = conn.cursor()

    c.execute("UPDATE usuarios SET salario=%s WHERE usuario=%s", (v, u))
    conn.commit()
    conn.close()


def atualizar_meta(u, v):
    conn = conectar()
    c = conn.cursor()

    c.execute("UPDATE usuarios SET meta=%s WHERE usuario=%s", (v, u))
    conn.commit()
    conn.close()


# ================= GASTOS =================
def salvar_gasto(u, data, cat, desc, valor, status):
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    INSERT INTO gastos (usuario,data,categoria,descricao,valor,status)
    VALUES (%s,%s,%s,%s,%s,%s)
    """, (u, data, cat, desc, valor, status))

    conn.commit()
    conn.close()


def listar_gastos(u):
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    SELECT data, categoria, descricao, valor, status 
    FROM gastos WHERE usuario=%s
    """, (u,))

    dados = c.fetchall()

    conn.close()
    return dados
