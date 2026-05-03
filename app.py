import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect("perfumes.db")
    conn.row_factory = sqlite3.Row
    return conn


def garantir_colunas():
    conn = get_db_connection()
    colunas = conn.execute("PRAGMA table_info(perfumes)").fetchall()
    nomes_colunas = [coluna["name"] for coluna in colunas]

    novas_colunas = {
        "link_compra": "TEXT",
        "ocasiao": "TEXT",
        "fixacao": "TEXT",
        "projecao": "TEXT",
        "notas": "TEXT"
    }

    for nome_coluna, tipo_coluna in novas_colunas.items():
        if nome_coluna not in nomes_colunas:
            conn.execute(f"ALTER TABLE perfumes ADD COLUMN {nome_coluna} {tipo_coluna}")

    conn.commit()
    conn.close()



@app.route("/")
def index():
    garantir_colunas()
    tipo = request.args.get("tipo")
    preco_min = request.args.get("preco_min")

    conn = get_db_connection()

    query = "SELECT * FROM perfumes WHERE 1=1"
    parametros = []

    if tipo:
        query += " AND tipo = ?"
        parametros.append(tipo)

    if preco_min:
        query += " AND preco >= ?"
        parametros.append(preco_min)

    perfumes = conn.execute(query, parametros).fetchall()
    conn.close()
    return render_template("index.html", perfumes=perfumes)


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
        preco = request.form["preco"]
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
                link_compra, ocasiao, fixacao, projecao, notas
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome, marca, tipo, preco, descricao, imagem,
                link_compra, ocasiao, fixacao, projecao, notas
            )
        )
        conn.commit()
        conn.close()

        return redirect(url_for("index"))
    return render_template("adicionar.html")

@app.route("/deletar/<int:id>")
def deletar(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM perfumes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
