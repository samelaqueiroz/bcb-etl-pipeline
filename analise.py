"""
Análise Exploratória dos Dados Carregados no Banco
Gera gráficos das séries históricas salvas pelo pipeline ETL.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

DB_PATH = "data/macroeconomico.db"
OUTPUT_DIR = "data/graficos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Paleta de cores por série
CORES = {
    "selic_meta":      "#E63946",
    "selic_diaria":    "#F4A261",
    "ipca":            "#2A9D8F",
    "cambio_dolar":    "#457B9D",
    "pib_crescimento": "#6A4C93",
    "inadimplencia":   "#E76F51",
}

TITULOS = {
    "selic_meta":      "Taxa Selic Meta (% a.a.)",
    "selic_diaria":    "Taxa Selic Diária (% a.a.)",
    "ipca":            "IPCA Acumulado 12 meses (%)",
    "cambio_dolar":    "Câmbio USD/BRL",
    "pib_crescimento": "PIB — Variação Trimestral (%)",
    "inadimplencia":   "Inadimplência PF — Total (%)",
}


def carregar_serie(nome: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT data, valor FROM indicadores WHERE serie = ? ORDER BY data",
        conn, params=(nome,)
    )
    conn.close()
    df["data"] = pd.to_datetime(df["data"])
    return df


def listar_series_disponiveis() -> list:
    conn = sqlite3.connect(DB_PATH)
    series = pd.read_sql("SELECT DISTINCT serie FROM indicadores", conn)["serie"].tolist()
    conn.close()
    return series


def plotar_serie(nome: str) -> None:
    df = carregar_serie(nome)
    if df.empty:
        print(f"Nenhum dado encontrado para: {nome}")
        return

    fig, ax = plt.subplots(figsize=(12, 4))
    cor = CORES.get(nome, "#333333")
    titulo = TITULOS.get(nome, nome)

    ax.plot(df["data"], df["valor"], color=cor, linewidth=1.8, alpha=0.9)
    ax.fill_between(df["data"], df["valor"], alpha=0.12, color=cor)

    # Anotar último valor
    ultimo = df.iloc[-1]
    ax.annotate(
        f'{ultimo["valor"]:.2f}',
        xy=(ultimo["data"], ultimo["valor"]),
        xytext=(8, 8), textcoords="offset points",
        fontsize=9, color=cor, fontweight="bold"
    )

    ax.set_title(titulo, fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Data", fontsize=9)
    ax.set_ylabel("Valor", fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b/%Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.xticks(rotation=30, ha="right", fontsize=8)
    plt.yticks(fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()

    caminho = os.path.join(OUTPUT_DIR, f"{nome}.png")
    plt.savefig(caminho, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Gráfico salvo: {caminho}")


def painel_completo() -> None:
    """Gera um painel 2×3 com todas as séries."""
    series = listar_series_disponiveis()
    if not series:
        print("Banco vazio. Execute o pipeline primeiro.")
        return

    n = len(series)
    cols = 2
    rows = (n + 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(16, rows * 3.5))
    axes = axes.flatten()
    fig.suptitle("Indicadores Macroeconômicos — BCB", fontsize=15, fontweight="bold", y=1.01)

    for i, nome in enumerate(series):
        df = carregar_serie(nome)
        if df.empty:
            continue

        ax = axes[i]
        cor = CORES.get(nome, "#555")
        ax.plot(df["data"], df["valor"], color=cor, linewidth=1.5)
        ax.fill_between(df["data"], df["valor"], alpha=0.1, color=cor)
        ax.set_title(TITULOS.get(nome, nome), fontsize=10, fontweight="bold")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, fontsize=7)
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        ax.spines[["top", "right"]].set_visible(False)

    # Esconde eixos extras
    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    plt.tight_layout()
    caminho = os.path.join(OUTPUT_DIR, "painel_completo.png")
    plt.savefig(caminho, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nPainel completo salvo: {caminho}")


def resumo_estatistico() -> None:
    """Exibe estatísticas descritivas de todas as séries."""
    series = listar_series_disponiveis()
    print("\n📈 Resumo Estatístico por Série\n" + "─" * 60)
    for nome in series:
        df = carregar_serie(nome)
        if df.empty:
            continue
        print(f"\n{TITULOS.get(nome, nome)}")
        print(f"  Período : {df['data'].min().date()} → {df['data'].max().date()}")
        print(f"  Registros: {len(df)}")
        print(f"  Mínimo  : {df['valor'].min():.4f}")
        print(f"  Máximo  : {df['valor'].max():.4f}")
        print(f"  Média   : {df['valor'].mean():.4f}")
        print(f"  Último  : {df['valor'].iloc[-1]:.4f}")


if __name__ == "__main__":
    resumo_estatistico()
    painel_completo()
    for s in listar_series_disponiveis():
        plotar_serie(s)
