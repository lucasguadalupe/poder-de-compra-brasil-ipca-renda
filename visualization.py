# visualization.py – Gráficos do projeto Poder de Compra Brasil
"""
Produz 4 figuras salvas em OUTPUT_DIR:
  1. painel_principal.png  – renda real vs nominal (base 100) + IPCA acumulado
  2. inflacao_mensal.png   – variação % mensal do IPCA com heatmap anual
  3. ganho_perda.png       – renda real: períodos de ganho (verde) e perda (vermelho)
  4. tabela_anual.png      – tabela resumo por ano
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from config import COLORS, EVENTS, OUTPUT_DIR


# ── setup global ─────────────────────────────────────────────────────────────

def _setup_style():
    plt.rcParams.update({
        "figure.facecolor":  COLORS["bg"],
        "axes.facecolor":    COLORS["bg"],
        "axes.edgecolor":    "#CBD5E1",
        "axes.labelcolor":   COLORS["text"],
        "axes.titlesize":    13,
        "axes.titleweight":  "bold",
        "axes.titlecolor":   COLORS["text"],
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "xtick.color":       COLORS["neutral"],
        "ytick.color":       COLORS["neutral"],
        "xtick.labelsize":   8,
        "ytick.labelsize":   8,
        "grid.color":        "#E2E8F0",
        "grid.linewidth":    0.6,
        "legend.frameon":    False,
        "legend.fontsize":   9,
        "font.family":       "DejaVu Sans",
    })


def _annotate_events(ax, df_index, events: dict, y_frac=0.97, fontsize=6.5):
    """Desenha linhas verticais e rótulos para eventos econômicos."""
    y_min, y_max = ax.get_ylim()
    y_pos = y_min + (y_max - y_min) * y_frac
    for date_str, label in events.items():
        try:
            dt = pd.Timestamp(date_str)
            if df_index.min() <= dt <= df_index.max():
                ax.axvline(dt, color=COLORS["event"], lw=1.0, ls="--", alpha=0.7, zorder=2)
                ax.text(dt, y_pos, label, fontsize=fontsize,
                        color=COLORS["event"], ha="center", va="top",
                        rotation=90, fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.15", fc=COLORS["bg"],
                                  ec=COLORS["event"], lw=0.5, alpha=0.85))
        except Exception:
            pass


def _save(fig, name: str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"      ✔ {path}")
    return path


# ── Figura 1 – Painel Principal ───────────────────────────────────────────────

def plot_painel_principal(df: pd.DataFrame, stats: dict) -> str:
    _setup_style()
    fig = plt.figure(figsize=(14, 9), facecolor=COLORS["bg"])
    fig.suptitle(
        "Evolução do Poder de Compra no Brasil",
        fontsize=17, fontweight="bold", color=COLORS["text"], y=0.98,
    )
    gs = gridspec.GridSpec(2, 1, figure=fig, hspace=0.38,
                           top=0.93, bottom=0.07, left=0.07, right=0.96)

    # ── subplot 1: índices base 100 ──
    ax1 = fig.add_subplot(gs[0])
    ax1.set_title(f"Renda Nominal vs Renda Real – Base 100 "
                  f"({stats['periodo_inicio']})", pad=8)

    ax1.plot(df.index, df["idx_nominal_100"], color=COLORS["nominal"],
             lw=2.2, label="Renda Nominal (R$ correntes)")
    ax1.plot(df.index, df["idx_real_100"],    color=COLORS["real"],
             lw=2.2, label="Renda Real (R$ constantes)")
    ax1.plot(df.index, df["idx_ipca_100"],    color=COLORS["inflation"],
             lw=1.5, ls="--", alpha=0.75, label="IPCA Acumulado")

    ax1.axhline(100, color=COLORS["neutral"], lw=0.8, ls=":")
    ax1.fill_between(df.index, df["idx_nominal_100"], df["idx_real_100"],
                     where=df["idx_nominal_100"] >= df["idx_real_100"],
                     alpha=0.10, color=COLORS["inflation"], label="Erosão inflacionária")

    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))
    ax1.set_ylabel("Índice (base = 100)")
    ax1.grid(True, axis="y")
    ax1.legend(loc="upper left", ncol=2)
    _annotate_events(ax1, df.index, EVENTS, y_frac=0.99)

    # ── subplot 2: IPCA acumulado % ──
    ax2 = fig.add_subplot(gs[1])
    ax2.set_title("IPCA Acumulado no Período (%)", pad=8)

    ax2.fill_between(df.index, df["ipca_acum_pct"],
                     color=COLORS["inflation"], alpha=0.18)
    ax2.plot(df.index, df["ipca_acum_pct"], color=COLORS["inflation"], lw=2.0)

    # rótulo do valor final
    last_val = df["ipca_acum_pct"].iloc[-1]
    ax2.annotate(f"{last_val:.0f}%",
                 xy=(df.index[-1], last_val),
                 xytext=(-40, 8), textcoords="offset points",
                 fontsize=9, color=COLORS["inflation"], fontweight="bold",
                 arrowprops=dict(arrowstyle="-", color=COLORS["inflation"], lw=0.8))

    ax2.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
    ax2.set_ylabel("Inflação acumulada (%)")
    ax2.grid(True, axis="y")
    _annotate_events(ax2, df.index, EVENTS, y_frac=0.97)

    # rodapé
    fig.text(0.5, 0.01,
             "Fonte: IBGE – IPCA (tabela 1737) e PNAD Contínua (tabela 5932)  |  Elaboração própria",
             ha="center", fontsize=7, color=COLORS["neutral"])
    return _save(fig, "01_painel_principal.png")


# ── Figura 2 – Inflação Mensal + Heatmap ─────────────────────────────────────

def plot_inflacao_mensal(df: pd.DataFrame) -> str:
    _setup_style()
    fig, axes = plt.subplots(2, 1, figsize=(14, 8),
                              gridspec_kw={"height_ratios": [3, 2], "hspace": 0.45},
                              facecolor=COLORS["bg"])
    fig.suptitle("Inflação Mensal (IPCA) – Variação % ao Mês",
                 fontsize=15, fontweight="bold", color=COLORS["text"], y=0.98)

    # ── barras mensais ──
    ax = axes[0]
    colors = [COLORS["inflation"] if v > 0 else COLORS["real"]
              for v in df["ipca_var"]]
    ax.bar(df.index, df["ipca_var"], color=colors, width=20, alpha=0.85)
    ax.axhline(0, color=COLORS["neutral"], lw=0.8)
    ax.axhline(df["ipca_var"].mean(), color=COLORS["nominal"],
               lw=1.2, ls="--", label=f"Média: {df['ipca_var'].mean():.2f}%")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=2))
    ax.set_ylabel("Variação % mensal")
    ax.legend()
    ax.grid(True, axis="y")
    _annotate_events(ax, df.index, EVENTS, y_frac=0.97)

    # ── heatmap anual ──
    ax2 = axes[1]
    anos   = sorted(df.index.year.unique())
    meses  = list(range(1, 13))
    matrix = np.full((len(anos), 12), np.nan)
    for i, ano in enumerate(anos):
        for j, mes in enumerate(meses):
            sel = df[(df.index.year == ano) & (df.index.month == mes)]
            if not sel.empty:
                matrix[i, j] = sel["ipca_var"].iloc[0]

    cmap = LinearSegmentedColormap.from_list(
        "ipca", ["#22C55E", "#F8FAFC", "#EF4444"], N=256)
    vmax = np.nanpercentile(np.abs(matrix), 95)
    im   = ax2.imshow(matrix, cmap=cmap, vmin=-vmax, vmax=vmax, aspect="auto")

    ax2.set_xticks(range(12))
    ax2.set_xticklabels(["Jan","Fev","Mar","Abr","Mai","Jun",
                          "Jul","Ago","Set","Out","Nov","Dez"], fontsize=8)
    ax2.set_yticks(range(len(anos)))
    ax2.set_yticklabels(anos, fontsize=8)
    ax2.set_title("Mapa de Calor – IPCA por Mês/Ano", pad=6, fontsize=11)

    for i in range(len(anos)):
        for j in range(12):
            if not np.isnan(matrix[i, j]):
                ax2.text(j, i, f"{matrix[i,j]:.1f}",
                         ha="center", va="center", fontsize=5.5,
                         color="white" if abs(matrix[i, j]) > vmax * 0.55 else COLORS["text"])

    plt.colorbar(im, ax=ax2, shrink=0.6, label="Var. % mensal")

    fig.text(0.5, 0.01,
             "Fonte: IBGE – IPCA (tabela 1737)  |  Elaboração própria",
             ha="center", fontsize=7, color=COLORS["neutral"])
    return _save(fig, "02_inflacao_mensal.png")


# ── Figura 3 – Ganho vs Perda de Poder de Compra ─────────────────────────────

def plot_ganho_perda(df: pd.DataFrame, stats: dict) -> str:
    _setup_style()
    fig, ax = plt.subplots(figsize=(14, 6), facecolor=COLORS["bg"])
    fig.suptitle("Renda Real – Períodos de Ganho e Perda de Poder de Compra",
                 fontsize=15, fontweight="bold", color=COLORS["text"], y=1.01)

    base = df["idx_real_100"].iloc[0]
    ax.axhline(100, color=COLORS["neutral"], lw=1.0, ls=":")

    # sombra de ganho/perda
    ax.fill_between(df.index, df["idx_real_100"], 100,
                    where=df["idx_real_100"] >= 100,
                    color=COLORS["gain"], alpha=0.6, label="Ganho de poder de compra")
    ax.fill_between(df.index, df["idx_real_100"], 100,
                    where=df["idx_real_100"] < 100,
                    color=COLORS["loss"], alpha=0.6, label="Perda de poder de compra")

    ax.plot(df.index, df["idx_real_100"], color=COLORS["real"],
            lw=2.2, zorder=4)
    ax.plot(df.index, df["idx_nominal_100"], color=COLORS["nominal"],
            lw=1.5, ls="--", alpha=0.6, label="Renda Nominal (ref.)")

    # anotação do resultado final
    final = df["idx_real_100"].iloc[-1]
    delta = final - 100
    cor   = COLORS["real"] if delta >= 0 else COLORS["inflation"]
    sinal = "▲" if delta >= 0 else "▼"
    ax.annotate(f"{sinal} {abs(delta):.1f} pts\n({stats['periodo_fim']})",
                xy=(df.index[-1], final),
                xytext=(-80, -30), textcoords="offset points",
                fontsize=9, color=cor, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=cor, lw=1.2))

    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))
    ax.set_ylabel("Índice renda real (base = 100)")
    ax.grid(True, axis="y")
    ax.legend(loc="upper left")
    _annotate_events(ax, df.index, EVENTS, y_frac=0.98)

    fig.text(0.5, -0.02,
             "Fonte: IBGE – IPCA (tabela 1737) e PNAD Contínua (tabela 5932)  |  Elaboração própria",
             ha="center", fontsize=7, color=COLORS["neutral"])
    plt.tight_layout()
    return _save(fig, "03_ganho_perda.png")


# ── Figura 4 – Tabela Anual ───────────────────────────────────────────────────

def plot_tabela_anual(anual: pd.DataFrame) -> str:
    _setup_style()
    fig, ax = plt.subplots(figsize=(12, len(anual) * 0.52 + 1.5),
                           facecolor=COLORS["bg"])
    ax.axis("off")
    ax.set_title("Resumo Anual – Inflação, Renda Nominal e Renda Real",
                 fontsize=13, fontweight="bold", color=COLORS["text"], pad=12)

    cols = ["IPCA\n(%a.a.)", "Renda\nNominal (R$)", "Renda\nReal (R$)",
            "Índice\nNominal", "Índice\nReal"]
    data = []
    for ano, row in anual.iterrows():
        data.append([
            f"{row['ipca_ano']:.1f}%",
            f"R$ {row['renda_nominal']:,.0f}",
            f"R$ {row['renda_real']:,.0f}",
            f"{row['idx_nominal']:.1f}",
            f"{row['idx_real']:.1f}",
        ])

    table = ax.table(
        cellText=data,
        rowLabels=[str(a) for a in anual.index],
        colLabels=cols,
        cellLoc="center",
        rowLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.45)

    # Colorir linhas alternadas e cabeçalho
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#CBD5E1")
        if row == 0:
            cell.set_facecolor(COLORS["text"])
            cell.set_text_props(color="white", fontweight="bold")
        elif col == -1:
            cell.set_facecolor("#E2E8F0")
            cell.set_text_props(fontweight="bold", color=COLORS["text"])
        elif row % 2 == 0:
            cell.set_facecolor("#F1F5F9")
        else:
            cell.set_facecolor(COLORS["bg"])

        # Colorir IPCA alto em vermelho claro
        if col == 0 and row > 0:
            try:
                ipca_val = anual.iloc[row - 1]["ipca_ano"]
                if ipca_val > 8:
                    cell.set_facecolor("#FEE2E2")
                elif ipca_val < 4:
                    cell.set_facecolor("#DCFCE7")
            except Exception:
                pass

    fig.text(0.5, 0.01,
             "Fonte: IBGE – IPCA (tabela 1737) e PNAD Contínua (tabela 5932)  |  Elaboração própria",
             ha="center", fontsize=7, color=COLORS["neutral"])
    return _save(fig, "04_tabela_anual.png")


# ── pipeline ──────────────────────────────────────────────────────────────────

def gerar_todos_os_graficos(df: pd.DataFrame, stats: dict,
                             anual: pd.DataFrame) -> list[str]:
    print("[3/4] Gerando visualizações...")
    paths = []
    paths.append(plot_painel_principal(df, stats))
    paths.append(plot_inflacao_mensal(df))
    paths.append(plot_ganho_perda(df, stats))
    paths.append(plot_tabela_anual(anual))
    print()
    return paths
