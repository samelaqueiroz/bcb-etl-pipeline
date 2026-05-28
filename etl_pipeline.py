"""
ETL Pipeline - Dados Macroeconômicos do Banco Central do Brasil
Fonte: API pública do BCB (SGS - Sistema Gerenciador de Séries Temporais)
Autora: Sâmela
"""

import requests
import pandas as pd
import sqlite3
import logging
import os
from datetime import datetime, timedelta

# ─── Configuração de Logging ───────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─── Configurações ─────────────────────────────────────────────────────────────
DB_PATH = "data/macroeconomico.db"
BCB_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"

# Séries disponíveis na API do BCB
SERIES = {
    "selic_meta":     {"codigo": 432,  "descricao": "Taxa Selic Meta (% a.a.)"},
    "selic_diaria":   {"codigo": 11,   "descricao": "Taxa Selic Diária (% a.a.)"},
    "ipca":           {"codigo": 433,  "descricao": "IPCA Acumulado 12 meses (%)"},
    "cambio_dolar":   {"codigo": 1,    "descricao": "Taxa de Câmbio USD/BRL (venda)"},
    "pib_crescimento":{"codigo": 4380, "descricao": "PIB - Variação Trimestral (%)"},
    "inadimplencia":  {"codigo": 21082,"descricao": "Inadimplência PF - Total (%)"},
}


# ─── EXTRACT ───────────────────────────────────────────────────────────────────
def extract(codigo: int, data_inicio: str, data_fim: str) -> pd.DataFrame | None:
    """Busca dados de uma série temporal na API do BCB."""
    url = BCB_URL.format(codigo=codigo)
    params = {
        "formato": "json",
        "dataInicial": data_inicio,
        "dataFinal": data_fim,
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if not data:
            logger.warning(f"Série {codigo}: nenhum dado retornado para o período.")
            return None
        df = pd.DataFrame(data)
        logger.info(f"Série {codigo}: {len(df)} registros extraídos.")
        return df
    except requests.exceptions.Timeout:
        logger.error(f"Série {codigo}: timeout na requisição.")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Série {codigo}: erro HTTP {e.response.status_code}.")
    except Exception as e:
        logger.error(f"Série {codigo}: erro inesperado — {e}")
    return None


# ─── TRANSFORM ─────────────────────────────────────────────────────────────────
def transform(df: pd.DataFrame, nome_serie: str, descricao: str) -> pd.DataFrame:
    """Limpa e padroniza o DataFrame extraído."""
    df = df.copy()

    # Renomear colunas
    df.columns = [c.lower() for c in df.columns]
    df.rename(columns={"data": "data", "valor": "valor"}, inplace=True)

    # Converter tipos
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"].str.replace(",", "."), errors="coerce")

    # Remover nulos
    antes = len(df)
    df.dropna(subset=["data", "valor"], inplace=True)
    removidos = antes - len(df)
    if removidos > 0:
        logger.warning(f"Série '{nome_serie}': {removidos} registros com dados inválidos removidos.")

    # Adicionar metadados
    df["serie"] = nome_serie
    df["descricao"] = descricao
    df["atualizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Ordenar
    df.sort_values("data", inplace=True)
    df.reset_index(drop=True, inplace=True)

    logger.info(f"Série '{nome_serie}': transformação concluída — {len(df)} registros válidos.")
    return df[["data", "serie", "descricao", "valor", "atualizado_em"]]


# ─── LOAD ──────────────────────────────────────────────────────────────────────
def load(df: pd.DataFrame, tabela: str = "indicadores") -> None:
    """Carrega os dados no banco SQLite."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        df_save = df.copy()
        df_save["data"] = df_save["data"].dt.strftime("%Y-%m-%d")

        # Upsert simples: apaga registros existentes da mesma série e reinserção
        serie = df_save["serie"].iloc[0]
        conn.execute(f"DELETE FROM {tabela} WHERE serie = ?", (serie,))

        df_save.to_sql(tabela, conn, if_exists="append", index=False)
        conn.commit()
        logger.info(f"Série '{serie}': {len(df_save)} registros carregados na tabela '{tabela}'.")
    except Exception as e:
        logger.error(f"Erro ao carregar dados no banco: {e}")
        conn.rollback()
    finally:
        conn.close()


def criar_tabela_se_nao_existir() -> None:
    """Garante que a tabela existe no banco antes de inserir dados."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS indicadores (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            data       TEXT NOT NULL,
            serie      TEXT NOT NULL,
            descricao  TEXT,
            valor      REAL,
            atualizado_em TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Banco de dados pronto.")


# ─── PIPELINE PRINCIPAL ────────────────────────────────────────────────────────
def run_pipeline(anos: int = 5) -> None:
    """Executa o pipeline completo para todas as séries configuradas."""
    data_fim = datetime.today()
    data_inicio = data_fim - timedelta(days=365 * anos)

    data_ini_str = data_inicio.strftime("%d/%m/%Y")
    data_fim_str = data_fim.strftime("%d/%m/%Y")

    logger.info("=" * 60)
    logger.info(f"INÍCIO DO PIPELINE — período: {data_ini_str} a {data_fim_str}")
    logger.info("=" * 60)

    criar_tabela_se_nao_existir()

    sucesso, falha = 0, 0

    for nome, info in SERIES.items():
        logger.info(f"Processando: {nome} ({info['descricao']})")
        df_raw = extract(info["codigo"], data_ini_str, data_fim_str)

        if df_raw is None:
            falha += 1
            continue

        df_clean = transform(df_raw, nome, info["descricao"])
        load(df_clean)
        sucesso += 1

    logger.info("=" * 60)
    logger.info(f"PIPELINE CONCLUÍDO — {sucesso} séries com sucesso, {falha} com falha.")
    logger.info("=" * 60)


# ─── CONSULTAS ÚTEIS ───────────────────────────────────────────────────────────
def consultar_ultima_leitura() -> None:
    """Exibe o último valor de cada série no banco."""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT serie, descricao, data, valor, atualizado_em
        FROM indicadores
        WHERE (serie, data) IN (
            SELECT serie, MAX(data) FROM indicadores GROUP BY serie
        )
        ORDER BY serie
    """
    df = pd.read_sql(query, conn)
    conn.close()
    print("\n📊 Últimos valores por série:\n")
    print(df.to_string(index=False))


def consultar_serie(nome: str) -> pd.DataFrame:
    """Retorna o histórico completo de uma série."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT data, valor FROM indicadores WHERE serie = ? ORDER BY data",
        conn, params=(nome,)
    )
    conn.close()
    return df


# ─── ENTRYPOINT ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_pipeline(anos=5)
    consultar_ultima_leitura()
