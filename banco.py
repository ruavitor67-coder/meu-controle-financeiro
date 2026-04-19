import sqlite3
import hashlib
import pandas as pd

def conectar():
    return sqlite3.connect('dados_app.db', check_same_thread=False)

def criar_tabelas():
    with conectar() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                     (usuario TEXT PRIMARY KEY, senha TEXT, nivel TEXT, salario REAL DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS gastos 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, data TEXT, 
                      categoria TEXT, descricao TEXT, valor REAL, status TEXT DEFAULT 'Pago')''')
        c.execute('''CREATE TABLE IF NOT EXISTS metas 
                     (usuario TEXT, categoria TEXT, limite REAL, PRIMARY KEY(usuario, categoria))''')
        
        try:
            c.execute("ALTER TABLE usuarios ADD COLUMN salario REAL DEFAULT 0")
        except:
            pass
            
        c.execute("SELECT usuario FROM usuarios WHERE usuario = 'admin'")
        if not c.fetchone():
            hash_padrao = hashlib.sha256("admin123".encode()).hexdigest()
            c.execute("INSERT INTO usuarios (usuario, senha, nivel, salario) VALUES ('admin', ?, 'admin', 0)", (hash_padrao,))
        
        conn.commit()

def validar_login(usuario, senha):
    with conectar() as conn:
        c = conn.cursor()
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        c.execute("SELECT nivel FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha_hash))
        res = c.fetchone()
        return res[0] if res else None

def adicionar_usuario(nome, senha, nivel):
    try:
        with conectar() as conn:
            c = conn.cursor()
            h = hashlib.sha256(senha.encode()).hexdigest()
            c.execute("INSERT INTO usuarios (usuario, senha, nivel, salario) VALUES (?, ?, ?, 0)", (nome, h, nivel))
            conn.commit()
            return True
    except:
        return False

def buscar_salario(usuario):
    with conectar() as conn:
        c = conn.cursor()
        c.execute("SELECT salario FROM usuarios WHERE usuario=?", (usuario,))
        res = c.fetchone()
        return res[0] if res else 0

def atualizar_salario(usuario, valor):
    with conectar() as conn:
        c = conn.cursor()
        c.execute("UPDATE usuarios SET salario=? WHERE usuario=?", (valor, usuario))
        conn.commit()

def salvar_gasto(usuario, data, categoria, descricao, valor, status='Pago'):
    with conectar() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO gastos (usuario, data, categoria, descricao, valor, status) VALUES (?, ?, ?, ?, ?, ?)",
                  (usuario, str(data), categoria, descricao, valor, status))
        conn.commit()

def buscar_gastos(usuario):
    with conectar() as conn:
        try:
            return pd.read_sql("SELECT id, data, categoria, descricao, valor, status FROM gastos WHERE usuario=?", conn, params=(usuario,))
        except:
            return pd.DataFrame(columns=['id', 'data', 'categoria', 'descricao', 'valor', 'status'])

def listar_usuarios():
    with conectar() as conn:
        return pd.read_sql("SELECT usuario, nivel, salario FROM usuarios", conn)

def alterar_senha_usuario(nome, nova_senha):
    with conectar() as conn:
        c = conn.cursor()
        h = hashlib.sha256(nova_senha.encode()).hexdigest()
        c.execute("UPDATE usuarios SET senha=? WHERE usuario=?", (h, nome))
        conn.commit()

def alterar_nivel_usuario(nome, nivel):
    with conectar() as conn:
        c = conn.cursor()
        c.execute("UPDATE usuarios SET nivel=? WHERE usuario=?", (nivel, nome))
        conn.commit()
        return True

def deletar_usuario(nome):
    if nome.lower() == 'admin': return False
    try:
        with conectar() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM gastos WHERE usuario=?", (nome,))
            c.execute("DELETE FROM usuarios WHERE usuario=?", (nome,))
            conn.commit()
            return True
    except:
        return False

def definir_meta(usuario, categoria, limite):
    with conectar() as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO metas VALUES (?, ?, ?)", (usuario, categoria, limite))
        conn.commit()

def buscar_metas(usuario):
    with conectar() as conn:
        try:
            return pd.read_sql("SELECT categoria, limite FROM metas WHERE usuario=?", conn, params=(usuario,))
        except:
            return pd.DataFrame(columns=['categoria', 'limite'])
