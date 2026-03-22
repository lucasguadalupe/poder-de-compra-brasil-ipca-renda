# report.py – Geração do mini-relatório econômico em texto
"""
Produz:
  • Relatório impresso no terminal
  • Arquivo output/relatorio.txt
"""

import os
from config import OUTPUT_DIR, EVENTS


SEPARADOR = "─" * 68


def _linha(label: str, valor: str, largura: int = 40) -> str:
    return f"  {label:<{largura}} {valor}"


def gerar_relatorio(stats: dict, anual) -> str:
    linhas = []

    def p(texto=""):
        linhas.append(texto)

    p("=" * 68)
    p("  RELATÓRIO: EVOLUÇÃO DO PODER DE COMPRA NO BRASIL")
    p(f"  Período analisado: {stats['periodo_inicio']} → {stats['periodo_fim']}")
    p("=" * 68)

    # ── 1. Inflação ──
    p()
    p("▌ 1. INFLAÇÃO (IPCA)")
    p(SEPARADOR)
    p(_linha("Inflação total no período:", f"{stats['ipca_total_pct']:.1f}%"))
    p(_linha("Inflação média anualizada:", f"{stats['ipca_aa_pct']:.1f}% a.a."))
    p(_linha("Meses analisados:", str(stats["meses_total"])))

    # ── 2. Renda ──
    p()
    p("▌ 2. RENDA MÉDIA")
    p(SEPARADOR)
    p(_linha("Renda nominal inicial:", f"R$ {stats['renda_inicial_nom']:,.0f}"))
    p(_linha("Renda nominal final:", f"R$ {stats['renda_final_nom']:,.0f}"))
    p(_linha("Variação nominal total:", f"+{stats['renda_nom_total']:.1f}%"))
    p()
    p(_linha("Renda real inicial (R$ constantes):", f"R$ {stats['renda_inicial_real']:,.0f}"))
    p(_linha("Renda real final (R$ constantes):", f"R$ {stats['renda_final_real']:,.0f}"))
    p(_linha("Variação real total:", _formata_variacao(stats['renda_real_total'])))

    # ── 3. Poder de Compra ──
    p()
    p("▌ 3. PODER DE COMPRA")
    p(SEPARADOR)
    saldo = stats["renda_real_total"]
    if saldo >= 0:
        p(f"  ✅ GANHO LÍQUIDO de poder de compra: +{saldo:.1f}%")
        interpretacao = ("A renda cresceu acima da inflação no período, "
                         "representando uma melhora real na capacidade de "
                         "consumo da população.")
    else:
        p(f"  ❌ PERDA LÍQUIDA de poder de compra: {saldo:.1f}%")
        interpretacao = ("A inflação corroeu parte da renda nominal, resultando "
                         "em deterioração real da capacidade de consumo.")
    p()
    p(f"  {interpretacao}")
    p()
    p(_linha("Meses com ganho real:", f"{stats['meses_ganho']} meses"))
    p(_linha("Meses com perda real:", f"{stats['meses_perda']} meses"))

    # ── 4. Melhores e Piores Momentos ──
    p()
    p("▌ 4. MELHORES E PIORES JANELAS DE 12 MESES")
    p(SEPARADOR)
    p(_linha("Melhor período (12 meses):",
             f"{stats['melhor_12m_val']:+.1f}%  → até {stats['melhor_12m_dt']}"))
    p(_linha("Pior período (12 meses):",
             f"{stats['pior_12m_val']:+.1f}%  → até {stats['pior_12m_dt']}"))

    # ── 5. Eventos Econômicos ──
    p()
    p("▌ 5. EVENTOS ECONÔMICOS MARCANTES NO PERÍODO")
    p(SEPARADOR)
    for data_str, label in EVENTS.items():
        label_clean = label.replace("\n", " ")
        p(f"  • {data_str}  –  {label_clean}")

    # ── 6. Tabela Anual ──
    p()
    p("▌ 6. RESUMO ANUAL")
    p(SEPARADOR)
    header = f"  {'Ano':>4}  {'IPCA':>7}  {'Renda Nom.':>12}  {'Renda Real':>12}  {'Idx Nom.':>8}  {'Idx Real':>8}"
    p(header)
    p("  " + "-" * 62)
    for ano, row in anual.iterrows():
        p(f"  {ano:>4}  {row['ipca_ano']:>6.1f}%"
          f"  R${row['renda_nominal']:>10,.0f}"
          f"  R${row['renda_real']:>10,.0f}"
          f"  {row['idx_nominal']:>7.1f}"
          f"  {row['idx_real']:>7.1f}")

    # ── 7. Conclusão ──
    p()
    p("▌ 7. INTERPRETAÇÃO ECONÔMICA")
    p(SEPARADOR)
    conclusao = _gerar_conclusao(stats)
    for parag in conclusao:
        p(f"  {parag}")
        p()

    p("=" * 68)
    p("  Fonte: IBGE – IPCA (tab. 1737) e PNAD Contínua (tab. 5932)")
    p("  Elaboração própria | Projeto: Análise de Poder de Compra Brasil")
    p("=" * 68)

    texto = "\n".join(linhas)
    print(texto)

    # Salva arquivo
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    caminho = os.path.join(OUTPUT_DIR, "relatorio.txt")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"\n  ✔ {caminho}")
    return texto


def _formata_variacao(val: float) -> str:
    return f"+{val:.1f}%" if val >= 0 else f"{val:.1f}%"


def _gerar_conclusao(stats: dict) -> list[str]:
    saldo = stats["renda_real_total"]
    ipca  = stats["ipca_total_pct"]
    nom   = stats["renda_nom_total"]

    paragrafos = []

    # Parágrafo 1 – visão geral
    p1 = (f"Entre {stats['periodo_inicio']} e {stats['periodo_fim']}, o Brasil "
          f"acumulou {ipca:.0f}% de inflação (IPCA), enquanto a renda nominal "
          f"média cresceu {nom:.0f}%. O resultado líquido sobre o poder de compra "
          f"foi de {_formata_variacao(saldo)}.")
    paragrafos.append(p1)

    # Parágrafo 2 – contexto macroeconômico
    paragrafos.append(
        "O período foi marcado por ciclos distintos: a recessão de 2015-2016 "
        "comprimiu salários reais; o choque da COVID-19 em 2020 afetou o mercado "
        "de trabalho, mas o Auxílio Emergencial sustentou a renda das famílias "
        "mais vulneráveis temporariamente. A reabertura econômica em 2021-2022 "
        "trouxe inflação elevada, corroendo poder de compra dos assalariados."
    )

    # Parágrafo 3 – interpretação do resultado
    if saldo >= 5:
        paragrafos.append(
            "O ganho real acumulado indica que a renda cresceu de forma "
            "estruturalmente acima da inflação, possivelmente refletindo "
            "expansão do mercado de trabalho formal e políticas de valorização "
            "do salário mínimo em parte do período."
        )
    elif saldo >= 0:
        paragrafos.append(
            "O ganho real modesto sugere que, embora a renda nominal tenha "
            "acompanhado a inflação de forma geral, houve períodos de deterioração "
            "significativa que limitaram a melhora estrutural do bem-estar."
        )
    else:
        paragrafos.append(
            "A perda real de poder de compra indica que a inflação superou o "
            "crescimento da renda nominal ao longo do período. Isso representa "
            "uma deterioração real do bem-estar médio, particularmente severa "
            "para famílias de renda fixa e classes mais baixas, que gastam "
            "proporcionalmente mais com itens de alta inflação (alimentos e energia)."
        )

    return paragrafos
