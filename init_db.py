import sqlite3

conn = sqlite3.connect("perfumes.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS perfumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    marca TEXT NOT NULL,
    tipo TEXT,
    preco REAL,
    descricao TEXT,
    imagem TEXT,
    link_compra TEXT
)
""")

colunas = conn.execute("PRAGMA table_info(perfumes)").fetchall()
nomes_colunas = [coluna[1] for coluna in colunas]

if "link_compra" not in nomes_colunas:
    conn.execute("ALTER TABLE perfumes ADD COLUMN link_compra TEXT")

quantidade = conn.execute("SELECT COUNT(*) FROM perfumes").fetchone()[0]

if quantidade == 0:
    conn.execute("""
    INSERT INTO perfumes (nome, marca, tipo, preco, descricao, imagem, link_compra)
    VALUES
    ('Acqua di Gio', 'Armani', 'citrico', 300, 'Fresco e elegante', 'acqua_di_gio.jpg', ''),
    ('CK One', 'Calvin Klein', 'fresco', 200, 'Leve e compartilhável', 'ck_one.jpg', ''),
    ('Natura Kaiak', 'Natura', 'citrico', 150, 'Perfeito para o dia a dia', 'kaiak_tradicional.jpg', '')
    """)

conn.commit()
conn.close()
