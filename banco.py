import sqlite3
import hashlib
import pandas as pd
import streamlit as st

def conectar():
    return sqlite3.connect('dados_app.db', check_same_thread=False)

def criar_tabelas():
    # Busca informações nos Secrets. Se não houver, usa o padrão admin/admin123
    admin_fixo = st.secrets.get("ADMIN_USER", "admin")
    senha_fixa = st.secrets.get("ADMIN_PASSWORD", "admin123")
    
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
            
        # Lógica de persistência:
        # 1. Verifica se o admin já existe para pegar o salário atual dele
        c.execute("SELECT salario FROM usuarios WHERE usuario = ?", (admin_fixo,))
        res = c.fetchone()
        salario_atual = res[0] if res else 0.0
        
        # 2. Atualiza ou Insere o admin com a senha dos Secrets
        # Isso garante que no reboot a senha do 'Secrets' seja a oficial
        hash_mestre = hashlib.sha256(senha_fixa.encode()).hexdigest()
        c.execute("""INSERT OR REPLACE INTO usuarios (usuario, senha, nivel, salario) 
                     VALUES (?, ?, 'admin', ?)""", (admin_fixo, hash_mestre, salario_atual))
        
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
    # Protege o usuário definido nos secrets de ser deletado
    admin_fixo = st.secrets.get("ADMIN_USER", "admin")
    if nome.lower() == admin_fixo.lower(): return False
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
