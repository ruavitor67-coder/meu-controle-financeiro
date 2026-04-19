import sqlite3
import hashlib
import pandas as pd

def conectar():
    return sqlite3.connect('dados_app.db', check_same_thread=False)

def criar_tabelas():
    conn = conectar()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (usuario TEXT PRIMARY KEY, senha TEXT, nivel TEXT, salario REAL DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS gastos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, data TEXT, 
                  categoria TEXT, descricao TEXT, valor REAL)''')
    # Tabela para metas
    c.execute('''CREATE TABLE IF NOT EXISTS metas 
                 (usuario TEXT, categoria TEXT, limite REAL, PRIMARY KEY(usuario, categoria))''')
    
    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN salario REAL DEFAULT 0")
    except: pass
    conn.commit()
    conn.close()

def atualizar_salario(usuario, valor):
    conn = conectar()
    c = conn.cursor()
    c.execute("UPDATE usuarios SET salario=? WHERE usuario=?", (valor, usuario))
    conn.commit()
    conn.close()

def buscar_salario(usuario):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT salario FROM usuarios WHERE usuario=?", (usuario,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0

def validar_login(usuario, senha):
    conn = conectar()
    c = conn.cursor()
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    c.execute("SELECT nivel FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha_hash))
    resultado = c.fetchone()
    conn.close()
    return resultado[0] if resultado else None

def salvar_gasto(usuario, data, categoria, descricao, valor):
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT INTO gastos (usuario, data, categoria, descricao, valor) VALUES (?, ?, ?, ?, ?)",
              (usuario, str(data), categoria, descricao, valor))
    conn.commit()
    conn.close()

def buscar_gastos(usuario):
    conn = conectar()
    df = pd.read_sql("SELECT * FROM gastos WHERE usuario=?", conn)
    conn.close()
    return df

def deletar_gasto(id_gasto):
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM gastos WHERE id=?", (id_gasto,))
    conn.commit()
    conn.close()

# --- FUNÇÕES DE METAS ---
def definir_meta(usuario, categoria, limite):
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO metas VALUES (?, ?, ?)", (usuario, categoria, limite))
    conn.commit()
    conn.close()

def buscar_metas(usuario):
    conn = conectar()
    df = pd.read_sql("SELECT categoria, limite FROM metas WHERE usuario=?", conn)
    conn.close()
    return df
