import fiiscraper as fscp
import pandas as pd
from fiiscraper.aws_uploader import upload_para_s3
import time

# --- CONFIGURAÇÃO ---
BUCKET_S3 = 'fii-data-bucket'

def run_pipeline():
    """
        Função principal que executa o pipeline de obtenção de dados.
    """
    print("--- INICIANDO PIPELINE DE DADOS DE FIIs ---")
    
    # Criando o Scraper (Métodos de raspagem dos dados)
    scraper = fscp.Scraper()

    # Listagem de FIIs disponíveis no site Fundamentus
    lista_fiis = scraper.listar_todos_fiis()

    # --- BUSCANDO DADOS ---
    print("--- INICIANDO BUSCA DOS DADOS DE FIIS IDENTIFICADOS ---")
    # Busca os dados de indicadores do dia
    indicadores_fiis = []
    for fii in lista_fiis:

        # Busca indicadores do FII
        indicadores_fii = scraper.buscar_indicadores_dia(fii.ticker)
        
        # Adiciona FII à lista
        indicadores_fiis.append(indicadores_fii)

    print("--- INICIANDO BUSCA DOS PREÇOS DOS FIIS ---")
    # Busca o histórico de preços para cada FII na lista
    preco_fiis = scraper.buscar_precos_em_lote(lista_fiis)

    # --- MARCANDO FIIS QUE TEM NO YFINANCE ---
    # Muda para 'tem_dados_yfinance = True' caso o FII tenha sido encontrado no yfinance
    for fii in lista_fiis:
        if fii.ticker in preco_fiis['ticker'].tolist():
            fii.tem_dados_yfinance = True

# Garante que o pipeline só seja executado quando o script for chamado diretamente
if __name__ == "__main__":
    start_time = time.perf_counter()
    run_pipeline()
    end_time = time.perf_counter()
    duration = end_time - start_time
    print(f"\n--- Pipeline de preços concluído em {duration:.2f} segundos ---")