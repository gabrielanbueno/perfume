import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "perfumes.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def converter_preco(valor):
    if not valor:
        return None

    try:
        return float(valor.replace(",", "."))
    except ValueError:
        return None


def garantir_colunas():
    conn = get_db_connection()
    colunas = conn.execute("PRAGMA table_info(perfumes)").fetchall()
    nomes_colunas = [coluna["name"] for coluna in colunas]

    novas_colunas = {
        "link_compra": "TEXT",
        "ocasiao": "TEXT",
        "fixacao": "TEXT",
        "projecao": "TEXT",
        "notas": "TEXT",
        "publico": "TEXT"
    }

    coluna_publico_criada = False

    for nome_coluna, tipo_coluna in novas_colunas.items():
        if nome_coluna not in nomes_colunas:
            conn.execute(f"ALTER TABLE perfumes ADD COLUMN {nome_coluna} {tipo_coluna}")
            if nome_coluna == "publico":
                coluna_publico_criada = True

    if coluna_publico_criada:
        conn.execute("""
            UPDATE perfumes
            SET publico = 'masculino'
            WHERE (publico IS NULL OR publico = '')
              AND (
                lower(nome) LIKE '%masculino%'
                OR lower(nome) LIKE '%homem%'
                OR lower(descricao) LIKE '%masculino%'
                OR lower(descricao) LIKE '%homem%'
                OR lower(tipo) = 'masculino'
              )
        """)
        conn.execute("""
            UPDATE perfumes
            SET publico = 'feminino'
            WHERE (publico IS NULL OR publico = '')
              AND (
                lower(nome) LIKE '%feminino%'
                OR lower(nome) LIKE '%mulher%'
                OR lower(descricao) LIKE '%feminino%'
                OR lower(descricao) LIKE '%mulher%'
                OR lower(tipo) = 'feminino'
              )
        """)
        conn.execute("""
            UPDATE perfumes
            SET publico = 'unissex'
            WHERE (publico IS NULL OR publico = '')
              AND (
                lower(nome) LIKE '%unissex%'
                OR lower(nome) LIKE '%unisex%'
                OR lower(descricao) LIKE '%unissex%'
                OR lower(descricao) LIKE '%unisex%'
                OR lower(tipo) = 'unissex'
                OR lower(tipo) = 'unisex'
              )
        """)

    conn.commit()
    conn.close()



@app.route("/")
def index():
    garantir_colunas()
    busca = request.args.get("busca", "").strip()
    tipo = request.args.get("tipo")
    publico = request.args.get("publico")
    preco_min = request.args.get("preco_min")
    preco_max = request.args.get("preco_max")

    conn = get_db_connection()

    query = "SELECT * FROM perfumes WHERE 1=1"
    parametros = []

    if busca:
        query += """
            AND (
                nome LIKE ?
                OR marca LIKE ?
                OR descricao LIKE ?
                OR notas LIKE ?
            )
        """
        termo = f"%{busca}%"
        parametros.extend([termo, termo, termo, termo])

    if tipo:
        query += " AND tipo = ?"
        parametros.append(tipo)

    if publico:
        query += " AND publico = ?"
        parametros.append(publico)

    preco_min_numero = converter_preco(preco_min)
    if preco_min_numero is not None:
        query += " AND preco >= ?"
        parametros.append(preco_min_numero)

    preco_max_numero = converter_preco(preco_max)
    if preco_max_numero is not None:
        query += " AND preco <= ?"
        parametros.append(preco_max_numero)

    query += " ORDER BY nome COLLATE NOCASE"
    perfumes = conn.execute(query, parametros).fetchall()
    tipos = conn.execute(
        "SELECT DISTINCT tipo FROM perfumes WHERE tipo IS NOT NULL AND tipo != '' ORDER BY tipo"
    ).fetchall()
    conn.close()
    filtros = {
        "busca": busca,
        "tipo": tipo or "",
        "publico": publico or "",
        "preco_min": preco_min or "",
        "preco_max": preco_max or "",
    }
    return render_template("index.html", perfumes=perfumes, tipos=tipos, filtros=filtros)


@app.route("/perfume/<int:id>")
def detalhe_perfume(id):
    garantir_colunas()
    conn = get_db_connection()
    perfume = conn.execute(
        "SELECT * FROM perfumes WHERE id = ?", (id,)
    ).fetchone()
    conn.close()
    return render_template("perfume.html", perfume=perfume)


@app.route("/adicionar", methods=["GET", "POST"])
def adicionar():
    garantir_colunas()
    if request.method == "POST":
        nome = request.form["nome"]
        marca = request.form["marca"]
        tipo = request.form["tipo"]
        publico = request.form["publico"]
        preco = converter_preco(request.form["preco"])
        descricao = request.form["descricao"]
        imagem = request.form["imagem"]
        link_compra = request.form["link_compra"]
        ocasiao = request.form["ocasiao"]
        fixacao = request.form["fixacao"]
        projecao = request.form["projecao"]
        notas = request.form["notas"]

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO perfumes (
                nome, marca, tipo, preco, descricao, imagem,
                link_compra, ocasiao, fixacao, projecao, notas, publico
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome, marca, tipo, preco, descricao, imagem,
                link_compra, ocasiao, fixacao, projecao, notas, publico
            )
        )
        conn.commit()
        conn.close()

        return redirect(url_for("index"))
    return render_template("adicionar.html")

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    garantir_colunas()

    conn = get_db_connection()
    perfume = conn.execute(
        "SELECT * FROM perfumes WHERE id = ?", (id,)
    ).fetchone()

    if perfume is None:
        conn.close()
        return redirect(url_for("index"))

    if request.method == "POST":
        nome = request.form["nome"]
        marca = request.form["marca"]
        tipo = request.form["tipo"]
        publico = request.form["publico"]
        preco = converter_preco(request.form["preco"])
        descricao = request.form["descricao"]
        imagem = request.form["imagem"]
        link_compra = request.form["link_compra"]
        ocasiao = request.form["ocasiao"]
        fixacao = request.form["fixacao"]
        projecao = request.form["projecao"]
        notas = request.form["notas"]

        conn.execute(
            """
            UPDATE perfumes
            SET nome = ?,
                marca = ?,
                tipo = ?,
                preco = ?,
                descricao = ?,
                imagem = ?,
                link_compra = ?,
                ocasiao = ?,
                fixacao = ?,
                projecao = ?,
                notas = ?,
                publico = ?
            WHERE id = ?
            """,
            (
                nome, marca, tipo, preco, descricao, imagem,
                link_compra, ocasiao, fixacao, projecao, notas, publico, id
            )
        )
        conn.commit()
        conn.close()

        return redirect(url_for("detalhe_perfume", id=id))

    conn.close()
    return render_template("editar.html", perfume=perfume)

@app.route("/deletar/<int:id>", methods=["POST"])
def deletar(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM perfumes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
