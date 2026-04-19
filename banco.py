import sqlite3
import hashlib
import pandas as pd

def conectar():
    return sqlite3.connect('dados_app.db', check_same_thread=False)

def criar_tabelas():
    conn = conectar()
    c = conn.cursor()
    # Tabela de usuários
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (usuario TEXT PRIMARY KEY, senha TEXT, nivel TEXT, salario REAL DEFAULT 0)''')
    # Tabela de gastos
    c.execute('''CREATE TABLE IF NOT EXISTS gastos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, data TEXT, 
                  categoria TEXT, descricao TEXT, valor REAL)''')
    # Tabela de metas
    c.execute('''CREATE TABLE IF NOT EXISTS metas 
                 (usuario TEXT, categoria TEXT, limite REAL, PRIMARY KEY(usuario, categoria))''')
    
    # Garante que a coluna salario existe
    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN salario REAL DEFAULT 0")
    except:
        pass

    senha_admin = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, nivel) VALUES ('admin', ?, 'admin')", (senha_admin,))
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

def listar_usuarios():
    conn = conectar()
    df = pd.read_sql("SELECT usuario, nivel, salario FROM usuarios", conn)
    conn.close()
    return df

def deletar_usuario(nome_usuario):
    if nome_usuario.lower().strip() == 'vitim': return False
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM gastos WHERE usuario=?", (nome_usuario,))
    c.execute("DELETE FROM usuarios WHERE usuario=?", (nome_usuario,))
    conn.commit()
    conn.close()
    return True

def alterar_senha_usuario(nome_usuario, nova_senha):
    conn = conectar()
    c = conn.cursor()
    nova_senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
    c.execute("UPDATE usuarios SET senha=? WHERE usuario=?", (nova_senha_hash, nome_usuario))
    conn.commit()
    conn.close()

def alterar_nivel_usuario(nome_usuario, novo_nivel):
    if nome_usuario.lower().strip() == 'vitim': return False
    conn = conectar()
    c = conn.cursor()
    c.execute("UPDATE usuarios SET nivel=? WHERE usuario=?", (novo_nivel, nome_usuario))
    conn.commit()
    conn.close()
    return True

def salvar_gasto(usuario, data, categoria, descricao, valor):
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT INTO gastos (usuario, data, categoria, descricao, valor) VALUES (?, ?, ?, ?, ?)",
              (usuario, str(data), categoria, descricao, valor))
    conn.commit()
    conn.close()

def buscar_gastos(usuario):
    conn = conectar()
    try:
        df = pd.read_sql("SELECT * FROM gastos WHERE usuario=?", conn, params=(usuario,))
    except:
        df = pd.DataFrame(columns=['id', 'usuario', 'data', 'categoria', 'descricao', 'valor'])
    conn.close()
    return df

def deletar_gasto(id_gasto):
    conn = conectar()
    c = conn.cursor()
    c.execute("DELETE FROM gastos WHERE id=?", (id_gasto,))
    conn.commit()
    conn.close()

def definir_meta(usuario, categoria, limite):
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO metas VALUES (?, ?, ?)", (usuario, categoria, limite))
    conn.commit()
    conn.close()

def buscar_metas(usuario):
    conn = conectar()
    try:
        df = pd.read_sql("SELECT categoria, limite FROM metas WHERE usuario=?", conn, params=(usuario,))
    except:
        df = pd.DataFrame(columns=['categoria', 'limite'])
    conn.close()
    return df
