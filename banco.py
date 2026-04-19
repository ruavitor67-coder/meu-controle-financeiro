import psycopg2
from passlib.hash import pbkdf2_sha256
import random
import smtplib
from email.mime.text import MIMEText


# ================= CONEXÃO =================
def conectar():
    return psycopg2.connect(
        host="aws-1-us-east-2.pooler.supabase.com",  # conexão direta
        database="postgres",
        user="postgres.gpmhnytpcbypqdocuxtq",
        password="Joseantony890@@",
        port=6543,
        sslmode="require"
    )


# ================= CRIAR TABELAS =================
def criar_tabelas():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        usuario TEXT UNIQUE,
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

    c.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id SERIAL PRIMARY KEY,
        usuario TEXT,
        nome TEXT,
        UNIQUE(usuario, nome)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS codigos (
        usuario TEXT,
        codigo TEXT
    )
    """)

    # cria admin padrão
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
def listar_usuarios():
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT usuario, nivel, salario, meta FROM usuarios")
    dados = c.fetchall()

    conn.close()

    import pandas as pd
    return pd.DataFrame(dados, columns=["usuario", "nivel", "salario", "meta"])


def adicionar_usuario(usuario, email, senha, nivel):
    conn = conectar()
    c = conn.cursor()

    senha_hash = pbkdf2_sha256.hash(senha)

    c.execute("""
    INSERT INTO usuarios (usuario, email, senha, nivel)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (usuario) DO NOTHING
    """, (usuario, email, senha_hash, nivel))

    conn.commit()
    conn.close()


def excluir_usuario(usuario):
    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM usuarios WHERE usuario=%s", (usuario,))
    conn.commit()
    conn.close()


def redefinir_senha(usuario, nova_senha):
    conn = conectar()
    c = conn.cursor()

    senha_hash = pbkdf2_sha256.hash(nova_senha)

    c.execute("UPDATE usuarios SET senha=%s WHERE usuario=%s",
              (senha_hash, usuario))

    conn.commit()
    conn.close()


def alterar_nivel(usuario, nivel):
    conn = conectar()
    c = conn.cursor()

    c.execute("UPDATE usuarios SET nivel=%s WHERE usuario=%s",
              (nivel, usuario))

    conn.commit()
    conn.close()


# ================= SALÁRIO / META =================
def buscar_salario(usuario):
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT salario FROM usuarios WHERE usuario=%s", (usuario,))
    r = c.fetchone()

    conn.close()
    return float(r[0]) if r else 0


def atualizar_salario(usuario, valor):
    conn = conectar()
    c = conn.cursor()

    c.execute("UPDATE usuarios SET salario=%s WHERE usuario=%s",
              (valor, usuario))

    conn.commit()
    conn.close()


def buscar_meta(usuario):
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT meta FROM usuarios WHERE usuario=%s", (usuario,))
    r = c.fetchone()

    conn.close()
    return float(r[0]) if r else 0


def atualizar_meta(usuario, valor):
    conn = conectar()
    c = conn.cursor()

    c.execute("UPDATE usuarios SET meta=%s WHERE usuario=%s",
              (valor, usuario))

    conn.commit()
    conn.close()


# ================= GASTOS =================
def salvar_gasto(usuario, data, categoria, descricao, valor, status):
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    INSERT INTO gastos (usuario, data, categoria, descricao, valor, status)
    VALUES (%s, %s, %s, %s, %s, %s)
    """, (usuario, data, categoria, descricao, valor, status))

    conn.commit()
    conn.close()


def buscar_gastos(usuario):
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    SELECT id, data, categoria, descricao, valor, status
    FROM gastos WHERE usuario=%s
    """, (usuario,))

    dados = c.fetchall()
    conn.close()

    import pandas as pd
    return pd.DataFrame(dados, columns=[
        "id", "data", "categoria", "descricao", "valor", "status"
    ])


def deletar_gasto(id):
    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM gastos WHERE id=%s", (id,))
    conn.commit()
    conn.close()


# ================= CATEGORIAS =================
def listar_categorias(usuario):
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT nome FROM categorias WHERE usuario=%s", (usuario,))
    dados = c.fetchall()

    conn.close()

    lista = [x[0] for x in dados] if dados else []

    # fallback padrão
    if not lista:
        lista = ["Alimentação", "Transporte", "Moradia", "Lazer"]

    return lista


def adicionar_categoria(usuario, nome):
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    INSERT INTO categorias (usuario, nome)
    VALUES (%s, %s)
    ON CONFLICT DO NOTHING
    """, (usuario, nome))

    conn.commit()
    conn.close()


# ================= RECUPERAÇÃO =================
def buscar_email(usuario):
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT email FROM usuarios WHERE usuario=%s", (usuario,))
    r = c.fetchone()

    conn.close()
    return r[0] if r else None


def gerar_codigo():
    return str(random.randint(100000, 999999))


def salvar_codigo(usuario, codigo):
    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM codigos WHERE usuario=%s", (usuario,))
    c.execute("INSERT INTO codigos VALUES (%s, %s)", (usuario, codigo))

    conn.commit()
    conn.close()


def validar_codigo(usuario, codigo):
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT codigo FROM codigos WHERE usuario=%s", (usuario,))
    r = c.fetchone()

    conn.close()

    return r and r[0] == codigo


# ================= EMAIL =================
def enviar_email(destino, codigo):
    try:
        msg = MIMEText(f"Seu código é: {codigo}")
        msg['Subject'] = "Recuperação de senha"
        msg['From'] = "seuemail@gmail.com"
        msg['To'] = destino

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login("seuemail@gmail.com", "SENHA_APP")
        server.sendmail(msg['From'], [destino], msg.as_string())
        server.quit()
    except Exception as e:
        print("Erro ao enviar email:", e)
