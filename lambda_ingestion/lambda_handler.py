import fiiscraper as fscp
import pandas as pd
from fiiscraper.aws_uploader import upload_df_to_s3
import logging
from fiiscraper.logger_config import setup_logging
from fiiscraper import Scraper
import time
import os
from datetime import date, timedelta

# Configura o logger
setup_logging()

def lambda_handler(event, context):
    """
    Ponto de entrada principal para a execução do AWS Lambda.
    Este handler orquestra o scraping e o upload para o S3.
    """
    logging.info("Iniciando a execução do Lambda de ingestão de FIIs...")

    try:
        # 1. Obter o nome do Bucket S3 a partir das Variáveis de Ambiente
        bucket_name = os.environ.get('BUCKET_S3')
        if not bucket_name:
            logging.error("Variável de ambiente 'BUCKET_S3' não definida.")
            raise ValueError("BUCKET_S3 não configurado.")

        logging.info(f"Conectando ao S3 Bucket: {bucket_name}")

        logging.info("--- STARTING FII DATA PIPELINE ---")
    
        # Creating the Scraper (Data scraping methods)
        scraper = fscp.Scraper()

        # Listing of FIIs available on the Fundamentus website
        lista_fiis = scraper.listar_todos_fiis()
        if not lista_fiis:
            logging.critical("Could not get the list of FIIs. Shutting down pipeline.")
            return

        # --- FETCHING DATA ---
        logging.info("--- STARTING TO FETCH DATA FOR IDENTIFIED FIIs ---")
        # Fetches the day's indicator data
        indicadores_fiis = []
        for fii in lista_fiis:

            # Fetches FII indicators
            indicadores_fii = scraper.buscar_indicadores_dia(fii.ticker)
            
            # Adds FII to the list
            indicadores_fiis.append(indicadores_fii)

        logging.info("--- STARTING TO FETCH FII PRICES ---")
        # Fetches the price history for each FII in the list
        preco_fiis = scraper.buscar_precos_em_lote([fii.ticker for fii in lista_fiis])

        # --- MARKING FIIs THAT ARE IN YFINANCE ---
        # Changes to 'tem_dados_yfinance = True' if the FII was found in yfinance
        for fii in lista_fiis:
            if fii.ticker in preco_fiis['ticker'].tolist():
                fii.tem_dados_yfinance = True

        # --- UPLOADING DATA TO S3 ---
        logging.info("--- STARTING DATA UPLOAD TO S3 ---")
        
        # Pega a data de hoje para usar nos nomes dos arquivos
        today = date.today()
        yesterday = date.today() - timedelta(days=1)

        # Indicadores diários
        if indicadores_fiis: 
            logging.info("Converting and sending daily statistics to S3...")
            try:
                # Converte a lista de objetos para um DataFrame do Pandas
                df_indicadores = pd.DataFrame([vars(fii) for fii in indicadores_fiis])
                # Força tipo da coluna para STRING, pois o campo tem algum valor que precisa ser tratado depo
                df_indicadores = df_indicadores.astype(str)

                # Define um nome de arquivo particionado (boa prática para data lakes)
                nome_arquivo_s3 = f'raw/daily_indicators/ingest_date={today.isoformat()}/data_parquet'
                
                # Chama a função de upload do seu módulo
                upload_df_to_s3(
                    df=df_indicadores,
                    bucket_name=bucket_name,  # Variável definida no topo do seu main.py
                    s3_filename=nome_arquivo_s3
                )
            except Exception as e:
                logging.error(f"Failed to process and upload indicators: {e}")
        else:
            logging.warning("No daily statistics data was collected.")

        # Dados de Preço
        if not preco_fiis.empty:
            logging.info("Sending daily prices to S3...")
            try:
                # Define um nome de arquivo particionado
                nome_arquivo_s3 = f'raw/price_history_snapshots/price_date={yesterday.isoformat()}/data_parquet'

                # Chama a função de upload
                upload_df_to_s3(
                    df=preco_fiis,
                    bucket_name=bucket_name,
                    s3_filename=nome_arquivo_s3
                )
            except Exception as e:
                logging.error(f"Failed to upload prices: {e}")
        else:
            logging.warning("No price data was collected.")

    except Exception as e:
        logging.error(f"Erro fatal durante a execução: {str(e)}")
        # Levanta a exceção para que o Lambda registre a execução como "Falha"
        raise e