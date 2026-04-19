import sqlite3
import hashlib
import pandas as pd  # <--- ADICIONE ESTA LINHA AQUI

def conectar():
    return sqlite3.connect('dados_app.db', check_same_thread=False)

def criar_tabelas():
    conn = conectar()
    c = conn.cursor()
    # Tabela de Usuários
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (usuario TEXT PRIMARY KEY, senha TEXT, cargo TEXT)''')
    # Tabela de Gastos
    c.execute('''CREATE TABLE IF NOT EXISTS gastos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, data TEXT, 
                  categoria TEXT, descricao TEXT, valor REAL)''')
    
    # Criar um Admin padrão se não existir (Senha: admin123)
    senha_hash = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO usuarios VALUES (?, ?, ?)", ("admin", senha_hash, "admin"))
    
    conn.commit()
    conn.close()

def adicionar_usuario(user, pw, cargo):
    conn = conectar()
    c = conn.cursor()
    senha_hash = hashlib.sha256(pw.encode()).hexdigest()
    try:
        c.execute("INSERT INTO usuarios VALUES (?, ?, ?)", (user, senha_hash, cargo))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def validar_login(user, pw):
    conn = conectar()
    c = conn.cursor()
    senha_hash = hashlib.sha256(pw.encode()).hexdigest()
    c.execute("SELECT cargo FROM usuarios WHERE usuario = ? AND senha = ?", (user, senha_hash))
    resultado = c.fetchone()
    conn.close()
    return resultado[0] if resultado else None

def salvar_gasto(user, data, cat, desc, val):
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT INTO gastos (usuario, data, categoria, descricao, valor) VALUES (?,?,?,?,?)",
              (user, str(data), cat, desc, val))
    conn.commit()
    conn.close()

def buscar_gastos(user, cargo):
    conn = conectar()
    # Se for admin, vê tudo. Se for user, vê só o dele.
    if cargo == 'admin':
        df = pd.read_sql_query("SELECT * FROM gastos", conn)
    else:
        df = pd.read_sql_query(f"SELECT * FROM gastos WHERE usuario = '{user}'", conn)
    conn.close()
    return df