# config.py – Configurações globais do projeto

# ── IBGE SIDRA API ────────────────────────────────────────────────────────────
SIDRA_BASE = "https://api.sidra.ibge.gov.br/values"

# IPCA mensal – variação % (v/2266) – âmbito Brasil (n1/all)
IPCA_URL = f"{SIDRA_BASE}/t/1737/n1/all/v/2266/p/all/f/u"

# PNAD Contínua – rendimento médio mensal real efetivo (tabela 5932)
# v/5929 = rendimento médio nominal; c2 = sexo total; c11913 = total
PNAD_URL = f"{SIDRA_BASE}/t/5932/n1/all/v/5929/p/all/c2/6794/c11913/allxt/f/u"

# ── PERÍODO DE ANÁLISE ────────────────────────────────────────────────────────
START_YEAR = 2012
END_YEAR   = 2024

# ── EVENTOS ECONÔMICOS RELEVANTES ────────────────────────────────────────────
EVENTS = {
    "2015-01": "Crise fiscal\nDilma",
    "2016-05": "Impeachment\nDilma",
    "2018-05": "Greve dos\ncaminhoneiros",
    "2020-03": "Pandemia\nCOVID-19",
    "2021-01": "Auxílio\nEmergencial",
    "2022-06": "Inflação\npico (12,1%)",
    "2023-01": "Lula III\nPosse",
}

# ── PALETA DE CORES ───────────────────────────────────────────────────────────
COLORS = {
    "nominal":   "#2563EB",   # azul
    "real":      "#16A34A",   # verde
    "inflation": "#DC2626",   # vermelho
    "neutral":   "#6B7280",   # cinza
    "gain":      "#BBF7D0",   # verde claro (fundo ganho)
    "loss":      "#FEE2E2",   # vermelho claro (fundo perda)
    "event":     "#F59E0B",   # âmbar (linha de evento)
    "bg":        "#F8FAFC",   # fundo geral
    "text":      "#1E293B",   # texto principal
}

OUTPUT_DIR = "output"
