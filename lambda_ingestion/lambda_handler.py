import fiiscraper as fscp
import pandas as pd
from fiiscraper.aws_uploader import upload_df_to_s3
import logging
from fiiscraper.logger_config import setup_logging
from fiiscraper import Scraper
import time
import os
from datetime import date, timedelta

# Configure the logger
setup_logging()

def lambda_handler(event, context):
    """
    Main entry point for the AWS Lambda execution.
    This handler orchestrates the scraping and upload to S3.
    """
    logging.info("Starting the FIIs ingestion Lambda execution...")

    try:
        # 1. Get the S3 Bucket name from Environment Variables
        bucket_name = os.environ.get('BUCKET_S3')
        if not bucket_name:
            logging.error("Environment variable 'BUCKET_S3' not set.")
            raise ValueError("BUCKET_S3 not configured.")

        logging.info(f"Connecting to S3 Bucket: {bucket_name}")

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
        
        # Get today's date to use in the filenames
        today = date.today()
        yesterday = date.today() - timedelta(days=1)

        # Daily indicators
        if indicadores_fiis: 
            logging.info("Converting and sending daily statistics to S3...")
            try:
                # Convert the list of objects to a Pandas DataFrame
                df_indicadores = pd.DataFrame([vars(fii) for fii in indicadores_fiis])
                # Force column type to STRING, as some fields may have values that need later treatment
                df_indicadores = df_indicadores.astype(str)

                # Define a partitioned filename (good practice for data lakes)
                nome_arquivo_s3 = f'raw/daily_indicators/ingest_date={today.isoformat()}/data_parquet'
                
                # Call the upload function from your module
                upload_df_to_s3(
                    df=df_indicadores,
                    bucket_name=bucket_name,  # Variable defined at the top of the handler
                    s3_filename=nome_arquivo_s3
                )
            except Exception as e:
                logging.error(f"Failed to process and upload indicators: {e}")
        else:
            logging.warning("No daily statistics data was collected.")

        # Price Data
        if not preco_fiis.empty:
            logging.info("Sending daily prices to S3...")
            try:
                # Define a partitioned filename
                nome_arquivo_s3 = f'raw/price_history_snapshots/price_date={yesterday.isoformat()}/data_parquet'

                # Call the upload function
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
        logging.error(f"Fatal error during execution: {str(e)}")
        # Raise the exception so that Lambda registers the execution as "Failed"
        raise e
