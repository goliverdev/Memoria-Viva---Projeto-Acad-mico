import sqlite3
from datetime import datetime


BANCO = "memoria_viva.db"

AVATARES_PADRAO = ["🙂", "🌿", "🌳", "🍃", "🌸", "🌻"]


def conectar():
    return sqlite3.connect(BANCO)


def _coluna_existe(cursor, tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = [linha[1] for linha in cursor.fetchall()]
    return coluna in colunas


def criar_banco():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            texto TEXT NOT NULL,
            emocao TEXT NOT NULL,
            data TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')

    conn.commit()

    # --- Migração segura: adiciona colunas novas sem apagar nada existente ---
    if not _coluna_existe(cursor, "usuarios", "avatar"):
        cursor.execute("ALTER TABLE usuarios ADD COLUMN avatar TEXT DEFAULT '🙂'")
    if not _coluna_existe(cursor, "usuarios", "data_cadastro"):
        cursor.execute("ALTER TABLE usuarios ADD COLUMN data_cadastro TEXT")
        cursor.execute(
            "UPDATE usuarios SET data_cadastro = ? WHERE data_cadastro IS NULL",
            (datetime.now().strftime("%d/%m/%Y"),)
        )
    if not _coluna_existe(cursor, "memorias", "frase_motivadora"):
        cursor.execute("ALTER TABLE memorias ADD COLUMN frase_motivadora TEXT DEFAULT ''")
    if not _coluna_existe(cursor, "memorias", "explicacao"):
        cursor.execute("ALTER TABLE memorias ADD COLUMN explicacao TEXT DEFAULT ''")
    if not _coluna_existe(cursor, "memorias", "visibilidade"):
        cursor.execute("ALTER TABLE memorias ADD COLUMN visibilidade TEXT DEFAULT 'privada'")

    conn.commit()
    conn.close()


def cadastrar_usuario(nome, email, senha, avatar=None):
    conn = conectar()
    cursor = conn.cursor()

    if not avatar:
        avatar = AVATARES_PADRAO[abs(hash(email)) % len(AVATARES_PADRAO)]
    data_cadastro = datetime.now().strftime("%d/%m/%Y")

    try:
        cursor.execute('''
        INSERT INTO usuarios 
        (nome, email, senha, avatar, data_cadastro)
        VALUES (?, ?, ?, ?, ?)''',
        (nome, email, senha, avatar, data_cadastro))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def fazer_login(email, senha):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT id, nome, email, senha, avatar, data_cadastro FROM usuarios 
    WHERE email = ? AND senha = ?
    ''',
    (email, senha))

    usuario = cursor.fetchone()

    conn.close()

    return usuario


def atualizar_usuario(usuario_id, nome, avatar):
    """Atualiza nome e avatar do usuário (usado na edição de perfil)."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE usuarios
    SET nome = ?, avatar = ?
    WHERE id = ?
    ''',
    (nome, avatar, usuario_id))

    conn.commit()
    conn.close()


def salvar_memoria(usuario_id, titulo, categoria, texto, emocao, data, frase_motivadora="", explicacao="", visibilidade="privada"):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO memorias 
    (usuario_id, titulo, categoria, texto, emocao, data, frase_motivadora, explicacao, visibilidade)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''',
    (usuario_id, titulo, categoria, texto, emocao, data, frase_motivadora, explicacao, visibilidade))

    conn.commit()
    conn.close()


def buscar_memorias(usuario_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT * 
    FROM memorias 
    WHERE usuario_id = ?
    ORDER BY data DESC
    ''',
    (usuario_id,))

    memorias = cursor.fetchall()

    conn.close()

    return memorias


def buscar_memorias_publicas(usuario_id_atual=None):
    """Retorna todas as memórias marcadas como 'publica', de qualquer
    usuário, junto com o nome e avatar de quem escreveu. Usado na tela
    de Comunidade para que histórias públicas possam ser encontradas
    por outras pessoas."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT memorias.*, usuarios.nome, usuarios.avatar
    FROM memorias
    JOIN usuarios ON memorias.usuario_id = usuarios.id
    WHERE memorias.visibilidade = 'publica'
    ORDER BY memorias.data DESC
    ''')

    memorias = cursor.fetchall()

    conn.close()

    return memorias

def pesquisar_memoria(usuario_id, titulo):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT * 
    FROM memorias 
    WHERE usuario_id = ? AND titulo LIKE ?
    ORDER BY data DESC
    ''',
    (usuario_id, f'%{titulo}%'))

    memorias_encontradas = cursor.fetchall()

    conn.close()

    return memorias_encontradas


def editar_memoria(id_memoria, titulo, categoria, texto, emocao, frase_motivadora=None):
    conn = conectar()
    cursor = conn.cursor()

    if frase_motivadora is None:
        cursor.execute('''
        UPDATE memorias 
        SET titulo = ?, 
            categoria = ?, 
            texto = ?, 
            emocao = ?
        WHERE id = ?
        ''',
        (titulo, categoria, texto, emocao, id_memoria))
    else:
        cursor.execute('''
        UPDATE memorias 
        SET titulo = ?, 
            categoria = ?, 
            texto = ?, 
            emocao = ?,
            frase_motivadora = ?
        WHERE id = ?
        ''',
        (titulo, categoria, texto, emocao, frase_motivadora, id_memoria))

    conn.commit()
    conn.close()


def excluir_memoria(id_memoria):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
    DELETE FROM memorias 
    WHERE id = ?
    ''',
    (id_memoria,))

    conn.commit()
    conn.close()


