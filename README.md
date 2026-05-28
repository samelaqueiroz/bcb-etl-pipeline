# 🏦 ETL Pipeline — Indicadores Macroeconômicos (BCB)

Pipeline de dados que extrai indicadores macroeconômicos da **API pública do Banco Central do Brasil**, transforma e carrega em um banco SQLite local, com suporte a agendamento automático.

---

## 📊 Dados coletados

| Série | Descrição |
|---|---|
| `selic_meta` | Taxa Selic Meta (% a.a.) |
| `selic_diaria` | Taxa Selic Diária (% a.a.) |
| `ipca` | IPCA Acumulado 12 meses (%) |
| `cambio_dolar` | Taxa de Câmbio USD/BRL |
| `pib_crescimento` | PIB — Variação Trimestral (%) |
| `inadimplencia` | Inadimplência PF — Total (%) |

Fonte: [SGS — Banco Central do Brasil](https://www.bcb.gov.br/estatisticas/tabelaespecial)

---

## 🏗️ Arquitetura

```
API BCB (JSON)
     │
     ▼
[EXTRACT]  →  requests + validação HTTP
     │
     ▼
[TRANSFORM] →  pandas: tipagem, limpeza, padronização
     │
     ▼
[LOAD]      →  SQLite (upsert por série)
     │
     ▼
[ANÁLISE]   →  matplotlib: gráficos e estatísticas
```

---

## 🚀 Como executar

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/bcb-etl-pipeline.git
cd bcb-etl-pipeline
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Execute o pipeline

```bash
# Execução única
python etl_pipeline.py

# Com agendamento automático (seg–sex, 8h e 18h)
python scheduler.py
```

### 4. Gere análises e gráficos

```bash
python analise.py
```

Os gráficos são salvos em `data/graficos/`.

---

## 📁 Estrutura do projeto

```
bcb-etl-pipeline/
│
├── etl_pipeline.py     # Pipeline principal (Extract → Transform → Load)
├── scheduler.py        # Agendador automático
├── analise.py          # Análise exploratória e visualizações
├── requirements.txt
│
├── data/
│   ├── macroeconomico.db   # Banco SQLite (gerado após execução)
│   └── graficos/           # Gráficos gerados
│
└── logs/
    └── pipeline.log        # Log de execuções
```

---

## 🛠️ Stack

- **Python 3.10+**
- **Pandas** — transformação de dados
- **Requests** — consumo da API REST do BCB
- **SQLite** — armazenamento local
- **Matplotlib** — visualizações
- **Schedule** — agendamento de tarefas

---

## 💡 Possíveis extensões

- [ ] Substituir SQLite por PostgreSQL
- [ ] Containerizar com Docker
- [ ] Adicionar alertas por e-mail quando Selic ou câmbio ultrapassar limiar
- [ ] Publicar dashboard interativo com Streamlit
- [ ] Orquestrar com Apache Airflow

---

## 📄 Licença

MIT
