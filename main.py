import fiiscraper as fscp
import pandas as pd
from fiiscraper.aws_uploader import upload_df_para_s3
import logging
from fiiscraper.logger_config import setup_logging
from fiiscraper import Scraper
import time
from datetime import date, timedelta

# --- CONFIGURATION ---
BUCKET_S3 = 'fii-data-bucket'

def run_pipeline():
    """
        Main function that runs the data acquisition pipeline.
    """
    # Logging setup
    setup_logging()
    
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
    # Daily statistics
    if not indicadores_fiis:
        logging.info("Sending daily statistics to S3...")
        # ...
    else:
        logging.warning("No daily statistics data was collected.")

    # Price data
    if not preco_fiis.empty:
        logging.info("Sending daily prices to S3...")
        # ...
    else:
        logging.warning("No price data was collected.")

# Ensures the pipeline only runs when the script is called directly
if __name__ == "__main__":
    start_time = time.perf_counter()
    run_pipeline()
    end_time = time.perf_counter()
    duration = end_time - start_time
    logging.info(f"\n--- Price pipeline finished in {duration:.2f} seconds ---")