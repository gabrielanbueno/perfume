🌿 Aura Cítrica - Blog.

Blog editorial sobre fragrâncias — desenvolvido com Flask + SQLite.

## Stack

- Python (Flask)
- SQLite
- HTML + CSS (Cormorant Garamond + Inter)

Design

Visual minimalista/clean de blog editorial:
- Tipografia: **Cormorant Garamond** (títulos, estilo italic) + **Inter** (corpo)
- Paleta: fundo `#FAFAF8`, texto `#1C1C1A`, acento dourado `#C4A882`
- Imagens padronizadas em proporção `16:9` (artigos) e `1:1` (cards de perfume)
- Traço dourado como assinatura visual nas seções

Execução

```bash
pip install -r requirements.txt
python init_db.py   # apenas na primeira vez
python app.py
```

Acesse: http://localhost:5000

Estrutura:
perfume/
├── app.py              # rotas Flask
├── init_db.py          # inicialização do banco
├── run_dev.py          # runner de desenvolvimento
├── perfumes.db         # banco SQLite (gerado)
├── static/
│   ├── style.css       # estilos do blog
│   └── imagens/        # imagens dos perfumes
└── templates/
    ├── base.html       # layout base
    ├── home.html       # página inicial
    ├── artigos.html    # lista de artigos
    ├── artigo.html     # artigo individual
    ├── index.html      # catálogo de perfumes
    ├── perfume.html    # detalhe do perfume
    ├── admin.html      # painel admin
    ├── adicionar.html  # formulário novo perfume
    ├── editar.html     # formulário editar perfume
    └── editar_artigo.html
