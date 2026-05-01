import sqlite3

conn = sqlite3.connect("perfumes.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS perfumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    tipo TEXT,
    preco REAL,
    descricao TEXT
)
""")

conn.execute("""
INSERT INTO perfumes (nome, tipo, preco, descricao)
VALUES 
('Acqua di Gio', 'citrico', 300, 'Fresco e elegante'),
('CK One', 'fresco', 200, 'Leve e compartilhável'),
('Natura Kaiak', 'citrico', 150, 'Perfeito para o dia a dia')
""")

conn.commit()
conn.close()