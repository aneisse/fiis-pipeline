import fiiscraper as fscp
import pandas as pd
from fiiscraper.aws_uploader import upload_df_para_s3
import logging
from fiiscraper.logger_config import setup_logging
from fiiscraper import Scraper
import time
from datetime import date, timedelta

# --- CONFIGURAÇÃO ---
BUCKET_S3 = 'fii-data-bucket'

def run_pipeline():
    """
        Função principal que executa o pipeline de obtenção de dados.
    """
    # Configuração do logging
    setup_logging()
    
    logging.info("--- INICIANDO PIPELINE DE DADOS DE FIIs ---")
    
    # Criando o Scraper (Métodos de raspagem dos dados)
    scraper = fscp.Scraper()

    # Listagem de FIIs disponíveis no site Fundamentus
    lista_fiis = scraper.listar_todos_fiis()
    if not lista_fiis:
        logging.critical("Não foi possível obter a lista de FIIs. Encerrando pipeline.")
        return

    # --- BUSCANDO DADOS ---
    logging.info("--- INICIANDO BUSCA DOS DADOS DE FIIS IDENTIFICADOS ---")
    # Busca os dados de indicadores do dia
    indicadores_fiis = []
    for fii in lista_fiis:

        # Busca indicadores do FII
        indicadores_fii = scraper.buscar_indicadores_dia(fii.ticker)
        
        # Adiciona FII à lista
        indicadores_fiis.append(indicadores_fii)

    logging.info("--- INICIANDO BUSCA DOS PREÇOS DOS FIIS ---")
    # Busca o histórico de preços para cada FII na lista
    preco_fiis = scraper.buscar_precos_em_lote([fii.ticker for fii in lista_fiis])

    # --- MARCANDO FIIS QUE TEM NO YFINANCE ---
    # Muda para 'tem_dados_yfinance = True' caso o FII tenha sido encontrado no yfinance
    for fii in lista_fiis:
        if fii.ticker in preco_fiis['ticker'].tolist():
            fii.tem_dados_yfinance = True

    # --- SUBINDO DADOS PARA O S3
    logging.info("--- INICIANDO ENIO DE DADOS PARA O S3 ---")
    # Estatísticas do dia
    if not indicadores_fiis:
        logging.info("Enviando estatísticas do dia para o S3...")
        # ...
    else:
        logging.warning("Nenhum dado de estatísticas do dia foi coletado.")

    # Dados de preço
    if not preco_fiis.empty:
        logging.info("Enviando preços diários para o S3...")
        # ...
    else:
        logging.warning("Nenhum dado de preço foi coletado.")

# Garante que o pipeline só seja executado quando o script for chamado diretamente
if __name__ == "__main__":
    start_time = time.perf_counter()
    run_pipeline()
    end_time = time.perf_counter()
    duration = end_time - start_time
    logging.info(f"\n--- Pipeline de preços concluído em {duration:.2f} segundos ---")