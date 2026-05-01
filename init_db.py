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
    imagem TEXT
)
""")

conn.execute("""
INSERT INTO perfumes (nome, marca, tipo, preco, descricao, imagem)
VALUES 
('Acqua di Gio', 'Armani', 'citrico', 300, 'Fresco e elegante', 'acqua.jpg'),
('CK One', 'Calvin Klein', 'fresco', 200, 'Leve e compartilhável', 'ckone.jpg'),
('Natura Kaiak', 'Natura', 'citrico', 150, 'Perfeito para o dia a dia', 'kaiak.jpg')
""")

conn.commit()
conn.close()