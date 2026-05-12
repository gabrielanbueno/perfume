import sqlite3
from pathlib import Path
import json
import re
from html import unescape
from urllib.error import URLError
from urllib.request import Request, urlopen
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "perfumes.db"

ARTIGOS = [
    {
        "slug": "perfumes-citricos-para-dias-quentes",
        "categoria": "Guia",
        "titulo": "Perfumes cítricos para dias quentes",
        "resumo": "Como escolher fragrâncias leves, frescas e confortáveis para calor, rotina e momentos ao ar livre.",
        "imagem": "acqua_fresca.jpg",
        "tempo": "4 min",
        "conteudo": [
            "Perfumes cítricos funcionam muito bem em dias quentes porque entregam sensação de limpeza, energia e leveza sem pesar na pele.",
            "Na prática, procure notas como bergamota, limão siciliano, laranja, mandarina, chá verde e acordes aquáticos. Elas costumam abrir com brilho e deixam a fragrância mais fácil de usar durante o dia.",
            "Para rotina, trabalho ou estudo, prefira projeção moderada e fixação equilibrada. O perfume não precisa dominar o ambiente para ser marcante.",
        ],
    },
    {
        "slug": "como-escolher-perfume-para-trabalho",
        "categoria": "Curadoria",
        "titulo": "Como escolher perfume para trabalho",
        "resumo": "Um guia direto para usar fragrância no escritório sem exagero: frescor, discrição e presença na medida.",
        "imagem": "ck_one.jpg",
        "tempo": "3 min",
        "conteudo": [
            "No trabalho, a melhor escolha costuma ser uma fragrância confortável: limpa, elegante e com projeção controlada.",
            "Perfumes frescos, cítricos, aromáticos suaves e aquáticos são bons caminhos. Eles passam cuidado pessoal sem competir com o espaço de outras pessoas.",
            "Aplique pouco, principalmente em ambientes fechados. Dois borrifos bem posicionados já podem ser suficientes.",
        ],
    },
    {
        "slug": "review-kaiak-masculino",
        "categoria": "Review",
        "titulo": "Review: Kaiak Masculino",
        "resumo": "Um clássico fresco da Natura para quem gosta de perfume fácil, versátil e com cara de movimento.",
        "imagem": "kaiak_tradicional.jpg",
        "tempo": "5 min",
        "conteudo": [
            "Kaiak Masculino é uma fragrância de proposta muito clara: frescor, praticidade e uso diário.",
            "Ele combina bem com calor, rotina, academia leve, trabalho informal e momentos casuais. Não é um perfume pesado, e essa é justamente a força dele.",
            "Vale para quem quer um perfume acessível, reconhecível e fácil de reaplicar ao longo do dia.",
        ],
    },
]


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def converter_preco(valor):
    if not valor:
        return None

    valor = str(valor).strip().replace("R$", "").replace(" ", "")
    if "," in valor and "." in valor:
        valor = valor.replace(".", "").replace(",", ".")
    else:
        valor = valor.replace(",", ".")

    try:
        return float(valor)
    except ValueError:
        return None


def gerar_slug(texto):
    texto = texto.lower().strip()
    substituicoes = {
        "á": "a", "à": "a", "â": "a", "ã": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for origem, destino in substituicoes.items():
        texto = texto.replace(origem, destino)
    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    return texto.strip("-") or "artigo"


def limpar_texto(texto):
    if not texto:
        return ""
    texto = re.sub(r"\s+", " ", texto)
    return unescape(texto).strip()


def extrair_meta(conteudo, propriedade):
    padrao = (
        rf'<meta[^>]+(?:property|name)=["\']{re.escape(propriedade)}["\'][^>]+content=["\']([^"\']+)["\']'
        rf'|<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(propriedade)}["\']'
    )
    encontrado = re.search(padrao, conteudo, re.IGNORECASE)
    if not encontrado:
        return ""
    return limpar_texto(encontrado.group(1) or encontrado.group(2))


def buscar_dados_produto(link):
    if not link:
        return {}

    requisicao = Request(
        link,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        },
    )

    try:
        with urlopen(requisicao, timeout=12) as resposta:
            conteudo = resposta.read().decode("utf-8", errors="ignore")
    except (URLError, TimeoutError, ValueError):
        return {}

    titulo = extrair_meta(conteudo, "og:title")
    imagem = extrair_meta(conteudo, "og:image")
    preco = extrair_meta(conteudo, "product:price:amount") or extrair_meta(
        conteudo, "price"
    )

    if not preco:
        json_ld = re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            conteudo,
            re.IGNORECASE | re.DOTALL,
        )
        for bloco in json_ld:
            try:
                dados = json.loads(bloco.strip())
            except json.JSONDecodeError:
                continue

            itens = dados if isinstance(dados, list) else [dados]
            for item in itens:
                ofertas = item.get("offers") if isinstance(item, dict) else None
                if isinstance(ofertas, dict) and ofertas.get("price"):
                    preco = str(ofertas["price"])
                    break
            if preco:
                break

    marca = ""
    nome = titulo
    if titulo and " - " in titulo:
        nome = titulo.split(" - ")[0].strip()
    elif titulo and " | " in titulo:
        nome = titulo.split(" | ")[0].strip()

    return {
        "nome": limpar_texto(nome),
        "marca": marca,
        "preco": preco.replace(".", ",") if preco else "",
        "imagem": imagem,
        "link_compra": link,
    }


def imagem_url(imagem):
    if not imagem:
        return url_for("static", filename="imagens/padrao.jpg")
    if imagem.startswith("http://") or imagem.startswith("https://"):
        return imagem
    return url_for("static", filename="imagens/" + imagem)


app.jinja_env.globals["imagem_url"] = imagem_url


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
        "publico": "TEXT",
        "promocao_dia": "INTEGER DEFAULT 0"
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


def garantir_tabelas_editoriais():
    garantir_colunas()
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS artigos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            categoria TEXT,
            titulo TEXT NOT NULL,
            resumo TEXT,
            imagem TEXT,
            tempo TEXT,
            conteudo TEXT,
            links_perfumes TEXT,
            destaque INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS artigo_perfumes (
            artigo_id INTEGER NOT NULL,
            perfume_id INTEGER NOT NULL,
            PRIMARY KEY (artigo_id, perfume_id),
            FOREIGN KEY (artigo_id) REFERENCES artigos(id) ON DELETE CASCADE,
            FOREIGN KEY (perfume_id) REFERENCES perfumes(id) ON DELETE CASCADE
        )
    """)

    colunas_artigos = conn.execute("PRAGMA table_info(artigos)").fetchall()
    nomes_artigos = [coluna["name"] for coluna in colunas_artigos]
    if "links_perfumes" not in nomes_artigos:
        conn.execute("ALTER TABLE artigos ADD COLUMN links_perfumes TEXT")

    quantidade = conn.execute("SELECT COUNT(*) FROM artigos").fetchone()[0]
    if quantidade == 0:
        for indice, artigo in enumerate(ARTIGOS):
            conn.execute(
                """
                INSERT INTO artigos (
                    slug, categoria, titulo, resumo, imagem, tempo, conteudo, links_perfumes, destaque
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artigo["slug"],
                    artigo["categoria"],
                    artigo["titulo"],
                    artigo["resumo"],
                    artigo["imagem"],
                    artigo["tempo"],
                    "\n\n".join(artigo["conteudo"]),
                    "",
                    1 if indice == 0 else 0,
                ),
            )

    conn.commit()
    conn.close()


def buscar_perfumes():
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

    query += " ORDER BY promocao_dia DESC, nome COLLATE NOCASE"
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
    return perfumes, tipos, filtros


def listar_destaques(limite=6):
    garantir_tabelas_editoriais()
    conn = get_db_connection()
    perfumes = conn.execute(
        """
        SELECT * FROM perfumes
        ORDER BY
            promocao_dia DESC,
            CASE WHEN link_compra IS NOT NULL AND link_compra != '' THEN 0 ELSE 1 END,
            nome COLLATE NOCASE
        LIMIT ?
        """,
        (limite,),
    ).fetchall()
    conn.close()
    return perfumes


def listar_artigos():
    garantir_tabelas_editoriais()
    conn = get_db_connection()
    artigos = conn.execute(
        """
        SELECT * FROM artigos
        ORDER BY destaque DESC, id DESC
        """
    ).fetchall()
    conn.close()
    return artigos


def buscar_artigo_por_slug(slug):
    garantir_tabelas_editoriais()
    conn = get_db_connection()
    artigo = conn.execute("SELECT * FROM artigos WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    return artigo


def buscar_artigo_por_id(artigo_id):
    garantir_tabelas_editoriais()
    conn = get_db_connection()
    artigo = conn.execute("SELECT * FROM artigos WHERE id = ?", (artigo_id,)).fetchone()
    conn.close()
    return artigo


def listar_todos_perfumes():
    garantir_colunas()
    conn = get_db_connection()
    perfumes = conn.execute(
        "SELECT id, nome, marca FROM perfumes ORDER BY nome COLLATE NOCASE"
    ).fetchall()
    conn.close()
    return perfumes


def listar_perfumes_do_artigo(artigo_id):
    garantir_tabelas_editoriais()
    conn = get_db_connection()
    perfumes = conn.execute(
        """
        SELECT p.*
        FROM perfumes p
        INNER JOIN artigo_perfumes ap ON ap.perfume_id = p.id
        WHERE ap.artigo_id = ?
        ORDER BY p.nome COLLATE NOCASE
        """,
        (artigo_id,),
    ).fetchall()
    conn.close()
    return perfumes


def ids_perfumes_do_artigo(artigo_id):
    return {perfume["id"] for perfume in listar_perfumes_do_artigo(artigo_id)}


def salvar_indicacoes_artigo(conn, artigo_id, perfume_ids):
    conn.execute("DELETE FROM artigo_perfumes WHERE artigo_id = ?", (artigo_id,))
    for perfume_id in perfume_ids:
        conn.execute(
            "INSERT OR IGNORE INTO artigo_perfumes (artigo_id, perfume_id) VALUES (?, ?)",
            (artigo_id, perfume_id),
        )


@app.route("/")
def index():
    artigos = listar_artigos()
    destaques = listar_destaques()
    return render_template("home.html", artigos=artigos, destaques=destaques)


@app.route("/perfumes")
def perfumes():
    perfumes, tipos, filtros = buscar_perfumes()
    return render_template("index.html", perfumes=perfumes, tipos=tipos, filtros=filtros)


@app.route("/admin")
def admin():
    perfumes, tipos, filtros = buscar_perfumes()
    artigos = listar_artigos()
    return render_template(
        "admin.html",
        perfumes=perfumes,
        tipos=tipos,
        filtros=filtros,
        artigos=artigos,
    )


@app.route("/artigos")
def artigos():
    return render_template("artigos.html", artigos=listar_artigos())


@app.route("/artigo/<slug>")
def artigo(slug):
    artigo_encontrado = buscar_artigo_por_slug(slug)
    if artigo_encontrado is None:
        return redirect(url_for("artigos"))

    perfumes_indicados = listar_perfumes_do_artigo(artigo_encontrado["id"])
    return render_template(
        "artigo.html",
        artigo=artigo_encontrado,
        artigos=listar_artigos(),
        perfumes_indicados=perfumes_indicados,
    )


@app.route("/admin/artigo/novo", methods=["GET", "POST"])
def novo_artigo():
    garantir_tabelas_editoriais()
    perfumes = listar_todos_perfumes()

    if request.method == "POST":
        titulo = request.form["titulo"].strip()
        slug = gerar_slug(request.form.get("slug") or titulo)
        perfume_ids = [int(valor) for valor in request.form.getlist("perfumes")]

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO artigos (
                slug, categoria, titulo, resumo, imagem, tempo, conteudo, links_perfumes, destaque
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slug,
                request.form["categoria"],
                titulo,
                request.form["resumo"],
                request.form["imagem"],
                request.form["tempo"],
                request.form["conteudo"],
                request.form["links_perfumes"],
                1 if request.form.get("destaque") else 0,
            ),
        )
        artigo_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        salvar_indicacoes_artigo(conn, artigo_id, perfume_ids)
        conn.commit()
        conn.close()
        return redirect(url_for("admin"))

    return render_template(
        "editar_artigo.html",
        artigo=None,
        perfumes=perfumes,
        perfumes_selecionados=set(),
    )


@app.route("/admin/artigo/<int:id>/editar", methods=["GET", "POST"])
def editar_artigo(id):
    garantir_tabelas_editoriais()
    artigo_encontrado = buscar_artigo_por_id(id)
    if artigo_encontrado is None:
        return redirect(url_for("admin"))

    perfumes = listar_todos_perfumes()
    perfumes_selecionados = ids_perfumes_do_artigo(id)

    if request.method == "POST":
        titulo = request.form["titulo"].strip()
        slug = gerar_slug(request.form.get("slug") or titulo)
        perfume_ids = [int(valor) for valor in request.form.getlist("perfumes")]

        conn = get_db_connection()
        conn.execute(
            """
            UPDATE artigos
            SET slug = ?,
                categoria = ?,
                titulo = ?,
                resumo = ?,
                imagem = ?,
                tempo = ?,
                conteudo = ?,
                links_perfumes = ?,
                destaque = ?
            WHERE id = ?
            """,
            (
                slug,
                request.form["categoria"],
                titulo,
                request.form["resumo"],
                request.form["imagem"],
                request.form["tempo"],
                request.form["conteudo"],
                request.form["links_perfumes"],
                1 if request.form.get("destaque") else 0,
                id,
            ),
        )
        salvar_indicacoes_artigo(conn, id, perfume_ids)
        conn.commit()
        conn.close()
        return redirect(url_for("admin"))

    return render_template(
        "editar_artigo.html",
        artigo=artigo_encontrado,
        perfumes=perfumes,
        perfumes_selecionados=perfumes_selecionados,
    )


@app.route("/admin/artigo/<int:id>/deletar", methods=["POST"])
def deletar_artigo(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM artigo_perfumes WHERE artigo_id = ?", (id,))
    conn.execute("DELETE FROM artigos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


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
    perfume_importado = {}
    if request.method == "POST":
        if request.form.get("acao") == "importar":
            perfume_importado = {
                "nome": request.form.get("nome", ""),
                "marca": request.form.get("marca", ""),
                "tipo": request.form.get("tipo", ""),
                "publico": request.form.get("publico", ""),
                "preco": request.form.get("preco", ""),
                "ocasiao": request.form.get("ocasiao", ""),
                "fixacao": request.form.get("fixacao", ""),
                "projecao": request.form.get("projecao", ""),
                "imagem": request.form.get("imagem", ""),
                "descricao": request.form.get("descricao", ""),
                "notas": request.form.get("notas", ""),
                "link_compra": request.form.get("link_compra", ""),
                "promocao_dia": 1 if request.form.get("promocao_dia") else 0,
            }
            dados_link = buscar_dados_produto(perfume_importado["link_compra"])
            perfume_importado.update(
                {chave: valor for chave, valor in dados_link.items() if valor}
            )
            return render_template("adicionar.html", perfume=perfume_importado)

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
        promocao_dia = 1 if request.form.get("promocao_dia") else 0

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO perfumes (
                nome, marca, tipo, preco, descricao, imagem,
                link_compra, ocasiao, fixacao, projecao, notas, publico, promocao_dia
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nome, marca, tipo, preco, descricao, imagem,
                link_compra, ocasiao, fixacao, projecao, notas, publico, promocao_dia
            )
        )
        conn.commit()
        conn.close()

        return redirect(url_for("admin"))
    return render_template("adicionar.html", perfume=perfume_importado)

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    garantir_colunas()

    conn = get_db_connection()
    perfume = conn.execute(
        "SELECT * FROM perfumes WHERE id = ?", (id,)
    ).fetchone()

    if perfume is None:
        conn.close()
        return redirect(url_for("admin"))

    if request.method == "POST":
        if request.form.get("acao") == "importar":
            perfume = dict(perfume)
            campos = [
                "nome", "marca", "tipo", "publico", "preco", "descricao",
                "imagem", "link_compra", "ocasiao", "fixacao", "projecao", "notas",
                "promocao_dia",
            ]
            for campo in campos:
                perfume[campo] = request.form.get(campo, "")
            dados_link = buscar_dados_produto(perfume["link_compra"])
            perfume.update({chave: valor for chave, valor in dados_link.items() if valor})
            conn.close()
            return render_template("editar.html", perfume=perfume)

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
        promocao_dia = 1 if request.form.get("promocao_dia") else 0

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
                publico = ?,
                promocao_dia = ?
            WHERE id = ?
            """,
            (
                nome, marca, tipo, preco, descricao, imagem,
                link_compra, ocasiao, fixacao, projecao, notas, publico, promocao_dia, id
            )
        )
        conn.commit()
        conn.close()

        return redirect(url_for("admin"))

    conn.close()
    return render_template("editar.html", perfume=perfume)

@app.route("/deletar/<int:id>", methods=["POST"])
def deletar(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM perfumes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True)
