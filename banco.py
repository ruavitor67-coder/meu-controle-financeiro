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
                  categoria TEXT, descricao TEXT, valor REAL, status TEXT DEFAULT 'Pago')''')
    c.execute('''CREATE TABLE IF NOT EXISTS metas 
                 (usuario TEXT, categoria TEXT, limite REAL, PRIMARY KEY(usuario, categoria))''')
    
    # Atualizações de colunas para evitar erros de leitura
    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN salario REAL DEFAULT 0")
    except: pass
    try:
        c.execute("ALTER TABLE gastos ADD COLUMN status TEXT DEFAULT 'Pago'")
    except: pass

    senha_admin = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, nivel) VALUES ('admin', ?, 'admin')", (senha_admin,))
    conn.commit()
    conn.close()

def validar_login(usuario, senha):
    conn = conectar()
    c = conn.cursor()
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    c.execute("SELECT nivel FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha_hash))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

def buscar_salario(usuario):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT salario FROM usuarios WHERE usuario=?", (usuario,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0

def atualizar_salario(usuario, valor):
    conn = conectar()
    c = conn.cursor()
    c.execute("UPDATE usuarios SET salario=? WHERE usuario=?", (valor, usuario))
    conn.commit()
    conn.close()

def salvar_gasto(usuario, data, categoria, descricao, valor, status='Pago'):
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT INTO gastos (usuario, data, categoria, descricao, valor, status) VALUES (?, ?, ?, ?, ?, ?)",
              (usuario, str(data), categoria, descricao, valor, status))
    conn.commit()
    conn.close()

def buscar_gastos(usuario):
    conn = conectar()
    try:
        # SELECT limpo para evitar o erro de DatabaseError das imagens
        df = pd.read_sql("SELECT id, data, categoria, descricao, valor, status FROM gastos WHERE usuario=?", conn, params=(usuario,))
    except:
        df = pd.DataFrame(columns=['id', 'data', 'categoria', 'descricao', 'valor', 'status'])
    finally:
        conn.close()
    return df

def listar_usuarios():
    conn = conectar()
    df = pd.read_sql("SELECT usuario, nivel, salario FROM usuarios", conn)
    conn.close()
    return df

def alterar_senha_usuario(nome, nova_senha):
    conn = conectar()
    c = conn.cursor()
    h = hashlib.sha256(nova_senha.encode()).hexdigest()
    c.execute("UPDATE usuarios SET senha=? WHERE usuario=?", (h, nome))
    conn.commit()
    conn.close()

def alterar_nivel_usuario(nome, nivel):
    if nome.lower().strip() == 'vitim': return False
    conn = conectar()
    c = conn.cursor()
    c.execute("UPDATE usuarios SET nivel=? WHERE usuario=?", (nivel, nome))
    conn.commit()
    conn.close()
    return True

def deletar_usuario(nome):
    nome_alvo = nome.lower().strip()
    if nome_alvo == 'vitim': return False # Proteção contra auto-exclusão
    
    conn = conectar()
    try:
        c = conn.cursor()
        # Remove dependências para não travar
        c.execute("DELETE FROM gastos WHERE usuario=?", (nome,))
        c.execute("DELETE FROM metas WHERE usuario=?", (nome,))
        c.execute("DELETE FROM usuarios WHERE usuario=?", (nome,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def definir_meta(usuario, categoria, limite):
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO metas VALUES (?, ?, ?)", (usuario, categoria, limite))
    conn.commit()
    conn.close()
