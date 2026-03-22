# analysis.py – Cálculos econômicos de poder de compra
"""
Recebe o DataFrame unificado e acrescenta:
  • renda_real          – renda deflacionada (R$ constantes do 1.º período)
  • idx_nominal_100     – índice renda nominal (base 100)
  • idx_real_100        – índice renda real    (base 100)
  • idx_ipca_100        – índice IPCA          (base 100)
  • variacao_real       – variação % mensal da renda real
  • poder_compra_delta  – diferença acumulada nominal × real (ganho/perda %)
  • periodo_tipo        – "ganho" | "perda" (para coloração)
"""

import pandas as pd
import numpy as np
from config import START_YEAR, END_YEAR


def deflacionar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deflaciona a renda nominal pelo IPCA acumulado.
    Renda real = Renda nominal / Índice de preços acumulado
    """
    df = df.copy()

    # índice de preços acumulado (base = 1 no primeiro mês)
    df["preco_idx"] = (1 + df["ipca_var"] / 100).cumprod()

    # renda real: R$ do 1.º mês do período
    df["renda_real"] = df["renda_nominal"] / df["preco_idx"]
    return df


def calcular_indices_base100(df: pd.DataFrame) -> pd.DataFrame:
    """Rebase todas as séries para 100 no primeiro mês disponível."""
    df = df.copy()
    base_nominal = df["renda_nominal"].iloc[0]
    base_real    = df["renda_real"].iloc[0]
    base_preco   = df["preco_idx"].iloc[0]

    df["idx_nominal_100"] = df["renda_nominal"] / base_nominal * 100
    df["idx_real_100"]    = df["renda_real"]    / base_real    * 100
    df["idx_ipca_100"]    = df["preco_idx"]     / base_preco   * 100
    return df


def identificar_periodos(df: pd.DataFrame, janela: int = 12) -> pd.DataFrame:
    """
    Rotula cada mês como período de 'ganho' ou 'perda' de poder de compra
    com base na variação acumulada da renda real em janela móvel de `janela` meses.
    """
    df = df.copy()
    df["variacao_real_acum"] = df["renda_real"].pct_change(janela) * 100
    df["periodo_tipo"] = df["variacao_real_acum"].apply(
        lambda x: "ganho" if pd.notna(x) and x > 0 else "perda"
    )
    return df


def resumo_por_ano(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa métricas-chave por ano para a tabela de relatório."""
    anual = df.resample("YE").agg(
        ipca_ano       = ("ipca_var", lambda s: ((1 + s / 100).prod() - 1) * 100),
        renda_nominal  = ("renda_nominal", "mean"),
        renda_real     = ("renda_real", "mean"),
        idx_nominal    = ("idx_nominal_100", "last"),
        idx_real       = ("idx_real_100", "last"),
    ).round(2)
    anual.index = anual.index.year
    anual.index.name = "Ano"
    return anual


def estatisticas_gerais(df: pd.DataFrame) -> dict:
    """Retorna dicionário com principais estatísticas do período."""
    ipca_total = (df["preco_idx"].iloc[-1] / df["preco_idx"].iloc[0] - 1) * 100
    renda_nom_total = (df["renda_nominal"].iloc[-1] / df["renda_nominal"].iloc[0] - 1) * 100
    renda_real_total = (df["renda_real"].iloc[-1] / df["renda_real"].iloc[0] - 1) * 100

    # meses de ganho / perda (variação mensal)
    df["var_real_mensal"] = df["renda_real"].pct_change() * 100
    meses_ganho = (df["var_real_mensal"] > 0).sum()
    meses_perda = (df["var_real_mensal"] < 0).sum()

    # pior e melhor período de 12 meses
    rolling_real = df["renda_real"].pct_change(12) * 100
    melhor_12m_val = rolling_real.max()
    melhor_12m_dt  = rolling_real.idxmax()
    pior_12m_val   = rolling_real.min()
    pior_12m_dt    = rolling_real.idxmin()

    # IPCA anualizado médio
    anos = (df.index[-1] - df.index[0]).days / 365.25
    ipca_aa = ((1 + ipca_total / 100) ** (1 / anos) - 1) * 100 if anos > 0 else 0

    return {
        "periodo_inicio":    df.index[0].strftime("%b/%Y"),
        "periodo_fim":       df.index[-1].strftime("%b/%Y"),
        "meses_total":       len(df),
        "ipca_total_pct":    round(ipca_total, 1),
        "ipca_aa_pct":       round(ipca_aa, 1),
        "renda_nom_total":   round(renda_nom_total, 1),
        "renda_real_total":  round(renda_real_total, 1),
        "ganho_perda_liq":   round(renda_real_total, 1),
        "meses_ganho":       int(meses_ganho),
        "meses_perda":       int(meses_perda),
        "melhor_12m_val":    round(melhor_12m_val, 1),
        "melhor_12m_dt":     melhor_12m_dt.strftime("%b/%Y"),
        "pior_12m_val":      round(pior_12m_val, 1),
        "pior_12m_dt":       pior_12m_dt.strftime("%b/%Y"),
        "renda_inicial_nom": round(df["renda_nominal"].iloc[0], 0),
        "renda_final_nom":   round(df["renda_nominal"].iloc[-1], 0),
        "renda_inicial_real":round(df["renda_real"].iloc[0], 0),
        "renda_final_real":  round(df["renda_real"].iloc[-1], 0),
    }


def pipeline(df: pd.DataFrame) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """
    Executa todo o pipeline analítico.
    Retorna: (df_enriquecido, stats_dict, tabela_anual)
    """
    print("[2/4] Executando análise econômica...")
    df = deflacionar(df)
    df = calcular_indices_base100(df)
    df = identificar_periodos(df)
    stats = estatisticas_gerais(df)
    anual = resumo_por_ano(df)
    print("      Análise concluída.\n")
    return df, stats, anual
