#!/usr/bin/env python3
# main.py – Ponto de entrada do projeto "Poder de Compra no Brasil"
"""
Uso:
    python main.py           # tenta API IBGE; usa dados reais offline se indisponível
    python main.py --offline # força modo offline com dados reais IBGE
    python main.py --help
"""

import sys
import os
import time

import data_collection as dc
import analysis
import visualization
import report
from config import OUTPUT_DIR


def banner():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║       ANÁLISE DE PODER DE COMPRA NO BRASIL  (2012 – 2024)       ║
║   Dados: IBGE – IPCA (tab. 1737) + PNAD Contínua (tab. 6390)   ║
║   Fallback offline: dados reais IBGE publicações oficiais        ║
╚══════════════════════════════════════════════════════════════════╝
""")


def main(force_offline: bool = False):
    banner()
    t0 = time.time()

    # ── 1. Coleta ─────────────────────────────────────────────────────────────
    if force_offline:
        df = dc.build_dataset_ibge_real()
    else:
        df = dc.build_dataset_with_fallback()

    if df.empty:
        print("[ERRO] Nenhum dado disponível. Encerrando.")
        sys.exit(1)

    # ── 2. Análise ────────────────────────────────────────────────────────────
    df, stats, anual = analysis.pipeline(df)

    # ── 3. Visualizações ──────────────────────────────────────────────────────
    caminhos = visualization.gerar_todos_os_graficos(df, stats, anual)

    # ── 4. Relatório ──────────────────────────────────────────────────────────
    print("[4/4] Gerando relatório econômico...\n")
    report.gerar_relatorio(stats, anual)

    # ── Resumo final ──────────────────────────────────────────────────────────
    elapsed = time.time() - t0
    print(f"\n{'─'*68}")
    print(f"  Projeto concluído em {elapsed:.1f}s")
    print(f"  Arquivos gerados em: ./{OUTPUT_DIR}/")
    for c in caminhos:
        print(f"    • {c}")
    print(f"    • {OUTPUT_DIR}/relatorio.txt")
    print(f"{'─'*68}\n")

    csv_path = os.path.join(OUTPUT_DIR, "dados_completos.csv")
    df.to_csv(csv_path, float_format="%.4f")
    print(f"  Dataset completo salvo em: {csv_path}\n")


if __name__ == "__main__":
    force = "--offline" in sys.argv or "-o" in sys.argv
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)
    main(force_offline=force)
