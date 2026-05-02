import sqlite3
from flask import Flask, render_template, request, redirect, url_for

#criação da aplocação 
app = Flask(__name__)

#função auxiliar com o banco de dados
def get_db_connection():
    conn = sqlite3.connect("perfumes.db")
    conn.row_factory = sqlite3.Row
    return conn

# Escopo principal
@app.route("/")
def index():
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

# Novo escopo
@app.route("/perfume/<int:id>")
def detalhe_perfume(id):
    conn = get_db_connection()
    perfume = conn.execute(
        "SELECT * FROM perfumes WHERE id = ?", (id,)
    ).fetchone()
    conn.close()
    return render_template("perfume.html", perfume=perfume)

#Escopo (pós) database
@app.route("/adicionar", methods=["GET", "POST"])
def adicionar():
    if request.method == "POST":
        nome = request.form["nome"]
        marca = request.form["marca"]
        tipo = request.form["tipo"]
        preco = request.form["preco"]
        descricao = request.form["descricao"]
        imagem = request.form["imagem"]
        
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO perfumes (nome, marca, tipo, preco, descricao, imagem) VALUES (?, ?, ?, ?, ?, ?)", (nome, marca, tipo, preco, descricao, imagem)
        )
        conn.commit()
        conn.close()
        
        return redirect(url_for("index"))
    return render_template("adicionar.html")

#Deletar
@app.route("/deletar/<int:id>")
def deletar(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM perfumes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)