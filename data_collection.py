# data_collection.py – Coleta de dados via API SIDRA/IBGE
"""
Busca dados de:
  • IPCA mensal          – tabela 1737 (variação %)
  • Renda nominal média  – PNAD Contínua tabela 5932
Devolve DataFrames com índice DatetimeIndex mensal.
"""

import requests
import pandas as pd
import numpy as np
from config import IPCA_URL, PNAD_URL, START_YEAR, END_YEAR


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_json(url: str, timeout: int = 30) -> list[dict]:
    """Faz GET na API SIDRA e devolve lista de dicts."""
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    # Primeira linha é cabeçalho na API SIDRA
    return data[1:]


def _parse_period(period_str: str) -> pd.Timestamp | None:
    """Converte 'YYYYMM' → Timestamp ou None."""
    s = str(period_str).strip()
    if len(s) == 6 and s.isdigit():
        return pd.Timestamp(year=int(s[:4]), month=int(s[4:]), day=1)
    return None


def _to_float(val) -> float:
    """Converte valor string para float, retorna NaN se inválido."""
    try:
        return float(str(val).replace(",", "."))
    except (ValueError, TypeError):
        return np.nan


# ── IPCA ─────────────────────────────────────────────────────────────────────

def fetch_ipca() -> pd.DataFrame:
    """
    Retorna DataFrame com colunas:
        data        – DatetimeIndex mensal
        ipca_var    – variação % mensal do IPCA
    """
    print("  → Buscando IPCA (tabela 1737)...")
    rows = _get_json(IPCA_URL)

    records = []
    for r in rows:
        dt = _parse_period(r.get("D3C") or r.get("D2C") or r.get("Mês (Código)"))
        val = _to_float(r.get("V") or r.get("Valor"))
        if dt and not np.isnan(val):
            records.append({"data": dt, "ipca_var": val})

    df = pd.DataFrame(records).drop_duplicates("data").sort_values("data")
    df = df[
        (df["data"].dt.year >= START_YEAR) &
        (df["data"].dt.year <= END_YEAR)
    ].reset_index(drop=True)

    # Inflação acumulada (índice, base = 100 no primeiro período)
    df["ipca_acum"] = (1 + df["ipca_var"] / 100).cumprod()
    df["ipca_acum_pct"] = (df["ipca_acum"] - 1) * 100

    print(f"     IPCA: {len(df)} observações "
          f"({df['data'].min().strftime('%b/%Y')} → {df['data'].max().strftime('%b/%Y')})")
    return df.set_index("data")


# ── PNAD Contínua – Renda Nominal ─────────────────────────────────────────────

def fetch_renda() -> pd.DataFrame:
    """
    Retorna DataFrame com colunas:
        data            – DatetimeIndex trimestral → interpolado para mensal
        renda_nominal   – rendimento médio mensal nominal (R$)
    """
    print("  → Buscando renda (PNAD Contínua – tabela 5932)...")
    rows = _get_json(PNAD_URL)

    records = []
    for r in rows:
        # período trimestral: ex. "201201" = 1º tri 2012
        periodo = str(r.get("D3C") or r.get("D2C") or "").strip()
        val = _to_float(r.get("V") or r.get("Valor"))

        # mapeia trimestre para mês central (ex.: "01"→jan, "02"→abr …)
        if len(periodo) == 6 and not np.isnan(val):
            year = int(periodo[:4])
            tri = int(periodo[4:])
            month_center = {1: 2, 2: 5, 3: 8, 4: 11}.get(tri)
            if month_center:
                dt = pd.Timestamp(year=year, month=month_center, day=1)
                records.append({"data": dt, "renda_nominal": val})

    df = (pd.DataFrame(records)
          .drop_duplicates("data")
          .sort_values("data")
          .set_index("data"))

    # Interpola para frequência mensal
    idx_mensal = pd.date_range(df.index.min(), df.index.max(), freq="MS")
    df = df.reindex(idx_mensal).interpolate(method="time")

    df = df[
        (df.index.year >= START_YEAR) &
        (df.index.year <= END_YEAR)
    ]

    print(f"     Renda: {len(df)} obs. mensais "
          f"({df.index.min().strftime('%b/%Y')} → {df.index.max().strftime('%b/%Y')})")
    return df


# ── Combinação ────────────────────────────────────────────────────────────────

def build_dataset() -> pd.DataFrame:
    """
    Une IPCA + Renda em um único DataFrame mensal alinhado.
    """
    print("\n[1/4] Coletando dados do IBGE...")
    ipca  = fetch_ipca()
    renda = fetch_renda()

    df = ipca.join(renda, how="inner")
    df.index.name = "data"
    print(f"\n  Dataset final: {len(df)} meses × {df.shape[1]} colunas\n")
    return df


# ── fallback / modo offline ───────────────────────────────────────────────────

def build_dataset_mock() -> pd.DataFrame:
    """
    Gera dados sintéticos realistas para testes offline.
    Usada automaticamente se a API SIDRA estiver indisponível.
    """
    print("\n  [AVISO] API indisponível – usando dados sintéticos realistas.\n")
    rng = pd.date_range("2012-01-01", "2024-12-01", freq="MS")
    n   = len(rng)
    np.random.seed(42)

    # IPCA: série com padrão histórico aproximado
    ipca_base = np.array([
        0.56, 0.45, 0.47, 0.55, 0.32, 0.08, 0.37, 0.38, 0.57, 0.59, 0.60, 0.79,  # 2012
        0.86, 0.60, 0.47, 0.55, 0.37, 0.26, 0.03, 0.24, 0.35, 0.56, 0.54, 0.92,  # 2013
        0.55, 0.69, 0.92, 0.67, 0.46, 0.40, 0.01, 0.25, 0.44, 0.42, 0.51, 0.78,  # 2014
        1.24, 1.22, 1.32, 0.71, 0.74, 0.79, 0.62, 0.22, 0.54, 0.82, 1.01, 0.96,  # 2015
        1.27, 0.90, 0.43, 0.61, 0.78, 0.35, 0.52, 0.44, 0.44, 0.26, 0.18, 0.30,  # 2016
        0.38, 0.33, 0.25, 0.14, 0.31, -0.23, 0.24, 0.19, 0.16, 0.42, 0.28, 0.44, # 2017
        0.29, 0.32, 0.09, 0.22, 0.40, 1.26, 0.33, -0.09, 0.48, 0.45, -0.21, 0.15,# 2018
        0.32, 0.43, 0.75, 0.57, 0.13, 0.01, 0.19, 0.11, -0.04, 0.10, 0.51, 1.15, # 2019
        0.21, 0.25, 0.07, -0.31, -0.38, 0.26, 0.36, 0.24, 0.64, 0.86, 0.89, 1.35,# 2020
        0.25, 0.86, 0.93, 0.31, 0.83, 0.53, 0.96, 0.87, 1.16, 1.25, 0.95, 0.73,  # 2021
        0.54, 1.01, 1.62, 1.06, 0.47, 0.67, -0.68, -0.73, -0.29, 0.59, 0.41, 0.62,# 2022
        0.53, 0.84, 0.71, 0.61, 0.23, -0.08, 0.12, 0.23, 0.26, 0.24, 0.28, 0.62, # 2023
        0.42, 0.83, 0.16, 0.38, 0.46, 0.20, 0.38, 0.44, 0.44, 0.56, 0.39, 0.52,  # 2024
    ])
    ipca_var = ipca_base[:n] + np.random.normal(0, 0.02, n)

    # Renda: cresce ~5% a.a. nominal com volatilidade
    renda0 = 1500.0
    renda_series = [renda0]
    for i in range(1, n):
        crescimento = 1 + (0.05 / 12) + np.random.normal(0, 0.003)
        renda_series.append(renda_series[-1] * crescimento)

    df = pd.DataFrame({
        "data": rng,
        "ipca_var":    ipca_var,
        "renda_nominal": renda_series,
    }).set_index("data")

    df["ipca_acum"]     = (1 + df["ipca_var"] / 100).cumprod()
    df["ipca_acum_pct"] = (df["ipca_acum"] - 1) * 100
    return df
