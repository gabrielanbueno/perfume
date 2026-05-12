import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

conn = sqlite3.connect(BASE_DIR / "perfumes.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS perfumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    marca TEXT NOT NULL,
    tipo TEXT,
    preco REAL,
    descricao TEXT,
    imagem TEXT,
    link_compra TEXT,
    ocasiao TEXT,
    fixacao TEXT,
    projecao TEXT,
    notas TEXT,
    publico TEXT,
    promocao_dia INTEGER DEFAULT 0
)
""")

colunas = conn.execute("PRAGMA table_info(perfumes)").fetchall()
nomes_colunas = [coluna[1] for coluna in colunas]

novas_colunas = {
    "link_compra": "TEXT",
    "ocasiao": "TEXT",
    "fixacao": "TEXT",
    "projecao": "TEXT",
    "notas": "TEXT",
    "publico": "TEXT",
    "promocao_dia": "INTEGER DEFAULT 0",
}

for nome_coluna, tipo_coluna in novas_colunas.items():
    if nome_coluna not in nomes_colunas:
        conn.execute(f"ALTER TABLE perfumes ADD COLUMN {nome_coluna} {tipo_coluna}")

quantidade = conn.execute("SELECT COUNT(*) FROM perfumes").fetchone()[0]

if quantidade == 0:
    conn.execute("""
    INSERT INTO perfumes (
        nome, marca, tipo, preco, descricao, imagem, link_compra,
        ocasiao, fixacao, projecao, notas, publico, promocao_dia
    )
    VALUES
    ('Acqua di Gio', 'Armani', 'citrico', 300, 'Fresco e elegante', 'acqua_di_gio.jpg', '', 'dia a dia', 'moderada', 'moderada', 'bergamota, jasmim, cedro', 'masculino', 0),
    ('CK One', 'Calvin Klein', 'fresco', 200, 'Leve e compartilhavel', 'ck_one.jpg', '', 'calor', 'suave', 'discreta', 'limao, cha verde, musk', 'unissex', 0),
    ('Natura Kaiak', 'Natura', 'citrico', 150, 'Perfeito para o dia a dia', 'kaiak_tradicional.jpg', '', 'rotina', 'moderada', 'moderada', 'notas aquaticas, ervas, musk', 'masculino', 0)
    """)

conn.commit()
conn.close()
