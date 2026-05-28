"""
Agendador do Pipeline ETL - Banco Central do Brasil
Executa automaticamente de segunda a sexta às 8h e às 18h.
"""

import schedule
import time
import logging
from etl_pipeline import run_pipeline

logger = logging.getLogger(__name__)


def job():
    logger.info("Agendador disparou execução do pipeline.")
    run_pipeline(anos=5)


def main():
    print("⏰ Agendador iniciado.")
    print("   Execuções agendadas: seg–sex às 08:00 e 18:00")
    print("   Pressione Ctrl+C para encerrar.\n")

    schedule.every().monday.at("08:00").do(job)
    schedule.every().tuesday.at("08:00").do(job)
    schedule.every().wednesday.at("08:00").do(job)
    schedule.every().thursday.at("08:00").do(job)
    schedule.every().friday.at("08:00").do(job)

    schedule.every().monday.at("18:00").do(job)
    schedule.every().tuesday.at("18:00").do(job)
    schedule.every().wednesday.at("18:00").do(job)
    schedule.every().thursday.at("18:00").do(job)
    schedule.every().friday.at("18:00").do(job)

    # Executa imediatamente na primeira vez
    job()

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
