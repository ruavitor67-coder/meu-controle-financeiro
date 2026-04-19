import sqlite3
import hashlib
import pandas as pd

def conectar():
    return sqlite3.connect('dados_app.db', check_same_thread=False)

def criar_tabelas():
    conn = conectar()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (usuario TEXT PRIMARY KEY, senha TEXT, nivel TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS gastos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, data TEXT, 
                  categoria TEXT, descricao TEXT, valor REAL)''')
    senha_admin = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', ?, 'admin')", (senha_admin,))
    conn.commit()
    conn.close()

def validar_login(usuario, senha):
    conn = conectar()
    c = conn.cursor()
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    c.execute("SELECT nivel FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha_hash))
    resultado = c.fetchone()
    conn.close()
    return resultado[0] if resultado else None

def adicionar_usuario(usuario, senha, nivel):
    try:
        conn = conectar()
        c = conn.cursor()
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        c.execute("INSERT INTO usuarios VALUES (?, ?, ?)", (usuario, senha_hash, nivel))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def salvar_gasto(usuario, data, categoria, descricao, valor):
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT INTO gastos (usuario, data, categoria, descricao, valor) VALUES (?, ?, ?, ?, ?)",
              (usuario, str(data), categoria, descricao, valor))
    conn.commit()
    conn.close()

def buscar_gastos(usuario, nivel):
    conn = conectar()
    # O 'id' precisa estar aqui!
    query = "SELECT id, data, categoria, descricao, valor FROM gastos WHERE usuario=?"
    df = pd.read_sql(query, conn, params=(usuario,))
    conn.close()
    return df

# NOVA FUNÇÃO PARA EXCLUIR
def deletar_gasto(id_gasto):
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM gastos WHERE id=?", (id_gasto,))
    conn.commit()
    conn.close()
