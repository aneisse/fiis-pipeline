import fiiscraper as fscp
import pandas as pd

def run_pipeline():
    """
        Função principal que executa o pipeline de obtenção de dados.
    """
    print("--- INICIANDO PIPELINE DE DADOS DE FIIs ---")
    
    # Criando o Scraper (Métodos de raspagem dos dados)
    scraper = fscp.Scraper()

    # Listagem de FIIs disponíveis no site Fundamentus
    lista_fiis = scraper.listar_todos_fiis()

    # Busca os dados de indicadores do dia
    indicadores_fiis = []
    for fii in lista_fiis:

        # Busca indicadores do FII
        indicadores_fii = scraper.buscar_indicadores_dia(fii.ticker)
        
        # Adiciona FII à lista
        indicadores_fiis.append(indicadores_fii)

    indicadores_fiis
    # Busca o histórico de preços para cada FII na lista
    historico_fiis = pd.DataFrame()
    for fii in lista_fiis:
        # Busca o histórico de preços  ods últimos 3 meses
        historico_fii = scraper.buscar_historico_precos(fii.ticker)

        # Insere o nome do ticker como primeira coluna
        historico_fii.insert(0, 'ticker', fii.ticker)

        # Adiciona os dados ao dataframe
        historico_fiis = pd.concat([historico_fiis, historico_fii])

# Garante que o pipeline só seja executado quando o script for chamado diretamente
if __name__ == "__main__":
    run_pipeline()
