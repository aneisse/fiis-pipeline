# Package imports
import requests
from bs4 import BeautifulSoup
from fiiscraper.models.fii import FII
import yfinance as yf
import pandas as pd
import logging
import re

# Creates a logger instance. The setup is done in main.py.
log = logging.getLogger(__name__)


class Scraper:
    """
    Class responsible for fund (FII) data gathering from multiple sources.
    """
    def __init__(self):
        # Source for the funds available for scraping
        self.url_lista_fiis = "https://www.fundamentus.com.br/fii_imoveis.php"

        # Base URL for fetching each fund's details page
        self.url_base_fii = "https://www.fundamentus.com.br/detalhes.php"  # Ex: ?papel=MXRF11

        # API URL for historic price fetching
        self.url_base_api_precos = "https://brapi.dev/api/quote/"  # Ex: MXRF11?range=3mo

        # Simulating a browser header.
        # Many sites block headerless requests
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/58.0.3029.110 Safari/537.36'
            )
        }

    # --- PUBLIC METHODS ---

    def listar_todos_fiis(self):
        """
        Gets a list of all funds (FIIs) listed on the Fundamentus website.

        Returns:
            list[FII]: A list of objects of FII class, each initialized with only the ticker.
        """
        log.info("Initiating the search for all FIIs on Fundamentus...")

        # Makes an HTTP request to get the page content
        response = self._buscar_html(self.url_lista_fiis)

        # Uses BeautifulSoup to parse the HTML
        soup = BeautifulSoup(response.text, 'lxml')

        # Finds the table that contains the funds data
        tabela = soup.find('table', {'id': 'tabelaFiiImoveis'})
        if not tabela:
            log.error("FII table not found on the page.")
            return []

        lista_de_fiis = []
        # Iterates over all rows (<tr>) from the table's body (<tbody>)
        # The [1:] would skip the first row (table header), but here we iterate all
        for linha in tabela.find('tbody').find_all('tr'):
            # Gets the first cell from each row (<td>), which contains the ticker
            celulas = linha.find_all('td')
            if celulas:
                ticker = celulas[0].text.strip()

                # Creates an FII object and adds it to the list
                novo_fii = FII(ticker=ticker)
                lista_de_fiis.append(novo_fii)

        lista_de_fiis = list(set(lista_de_fiis))  # Removes duplicates

        log.info(f"{len(lista_de_fiis)} FIIs found.")
        return lista_de_fiis

    def buscar_indicadores_dia(self, ticker: str):
        """
        Fetch indicators for a specific fund (FII) on Fundamentus.
        Returns an object of class FII.

        Args:
            ticker (str): The ticker of the fund
        """
        log.info(f"Fetching indicators for {ticker}...")
        # Building the URL according to the Fundamentus website structure
        url_fii = f"{self.url_base_fii}?papel={ticker}"
    
        # Makes the HTTP request to get the page content
        response = self._buscar_html(url_fii)
        if not response:
            return None

        # Uses the private method to parse the HTML
        indicadores_fii = self._parsear_pagina_fii(response.text)
        if not indicadores_fii  or 'Cotação' not in indicadores_fii:
            log.warning(f"  > Main content not found for {ticker}. Ticker is probably invalid.")
            return None

        # Cleans and converts data types
        indicadores_limpos = self._limpar_e_converter_dados(indicadores_fii)

        # Populates the FII object with the data
        fii = FII(ticker=ticker)
        # General data
        fii.nome = indicadores_limpos.get('Nome')
        fii.mandato = indicadores_limpos.get('Mandato')
        fii.segmento = indicadores_limpos.get('Segmento')
        fii.tipo_gestao = indicadores_limpos.get('Gestão')

        # Price indicators
        fii.cotacao = indicadores_limpos.get('Cotação')
        fii.data_ult_cotacao = indicadores_limpos.get('Data últ cot')
        fii.min_52_semanas = indicadores_limpos.get('Min 52 sem')
        fii.max_52_semanas = indicadores_limpos.get('Max 52 sem')
        fii.volume_medio_2meses = indicadores_limpos.get('Vol $ méd (2m)')
        fii.valor_mercado = indicadores_limpos.get('Valor de mercado')
        fii.numero_cotas = indicadores_limpos.get('Nro. Cotas')
        # fii.data_ult_relatorio_gerencial = indicadores_limpos.get('')
        fii.data_ult_info_trimestral = indicadores_limpos.get('Últ Info Trimestral')
        fii.var_dia = indicadores_limpos.get('Dia')
        fii.var_mes = indicadores_limpos.get('Mês')
        fii.var_30_dias = indicadores_limpos.get('30 dias')
        fii.var_12_meses = indicadores_limpos.get('12 meses')

        # Yield indicators
        fii.ffo_yield = indicadores_limpos.get('FFO Yield')
        fii.ffo_cota = indicadores_limpos.get('FFO/Cota')
        fii.div_yield = indicadores_limpos.get('FFO Yield')
        fii.div_cota = indicadores_limpos.get('Dividendo/cota')
        fii.p_vp = indicadores_limpos.get('P/VP')
        fii.vp_cota = indicadores_limpos.get('VP/Cota')

        # Revenue indicators
        fii.receita_12_meses = indicadores_limpos.get('Receita')
        fii.venda_ativos_12_meses = indicadores_limpos.get('Venda de ativos')
        fii.ffo_12_meses = indicadores_limpos.get('FFO')
        fii.rendimento_distribuido_12_meses = indicadores_limpos.get('Rend. Distribuído')
        fii.receita_3_meses = indicadores_limpos.get('Receita_2')
        fii.venda_ativos_3_meses = indicadores_limpos.get('Venda de ativos_2')
        fii.ffo_3_meses = indicadores_limpos.get('FFO_2')
        fii.rendimento_distribuido_3_meses = indicadores_limpos.get('Rend. Distribuído_2')

        # Net equity
        fii.ativos = indicadores_limpos.get('Ativos')
        fii.patrimonio_liquido = indicadores_limpos.get('Patrim Líquido')

        # Real estate indicators
        fii.qtd_imoveis = indicadores_limpos.get('Qtd imóveis')
        fii.qtd_unidades = indicadores_limpos.get('Qtd Unidades')
        fii.imoveis_pl = indicadores_limpos.get('Imóveis/PL do FII')
        fii.metros_quadrados = indicadores_limpos.get('Área (m2)')
        fii.aluguel_metro_quadrado = indicadores_limpos.get('Aluguel/m2')
        fii.preco_metro_quadrado = indicadores_limpos.get('Preço do m2')
        fii.cap_rate = indicadores_limpos.get('Cap Rate')
        fii.vacancia_media = indicadores_limpos.get('Vacância Média')

        return fii

    def buscar_precos_em_lote(self, tickers: list[str]) -> pd.DataFrame:
        """
        Fetches the most recent closing price for a list of tickers in an optimized way,
        performing a single batch download.

        Args:
            tickers (list[str]): A list of FII tickers (e.g., ['MXRF11', 'HGLG11']).

        Returns:
            pd.DataFrame: A DataFrame containing 'ticker', 'date', 'close', and 'volume'
                  for all tickers found. Returns an empty DataFrame in case of error.
        """
        log.info(f"Fetching for recent prices in batch for {len(tickers)} tickers via yfinance...")
        if not tickers:
            return pd.DataFrame()

        try:
            # Adds the '.SA' suffix to all tickers for yfinance compatibility
            tickers_sa = [f"{ticker}.SA" for ticker in tickers]

            # Downloads the tickers in a batch. yf.Tickers().download is faster for multiple tickers.
            # It gets 5 days toa ssure we got the last working day on the window.
            df_lote = yf.Tickers(tickers_sa).download(period="30d", progress=False, auto_adjust=False)

            if df_lote.empty:
                return pd.DataFrame()

            # Restructures the data
            df_final = df_lote.stack(future_stack=True).reset_index()
            df_final

            # Renames the columns
            df_final.columns = [col.lower() for col in df_final.columns]

            # Drops rows with no 'close' price
            df_final = df_final.dropna(subset=['close'])

            # Gets the most recent entry for each ticker
            df_final = df_final.loc[df_final.groupby('ticker')['date'].idxmax()]

            # Removes the '.SA' suffix from the ticker names
            df_final['ticker'] = df_final['ticker'].str.replace('.SA', '', regex=False)

            # Formats the date
            df_final['date'] = df_final['date'].dt.strftime('%Y-%m-%d')

            log.info(f"  > Prices for {len(df_final)} tickers successfully found.")
            return df_final

        except Exception as e:
            log.error(f"  > An error occurred during the batch download from yfinance: {e}")
            return pd.DataFrame()

    # --- PRIVATE METHODS ---

    def _buscar_html(self, url: str):
        """Helper method to make the HTTP request and return the HTML."""

        log.debug(f" > Accessing URL: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()  # Raises an error for bad status codes (404, 500, etc.)
            return response
        except requests.RequestException as e:
            log.error(f"Error during request of URL: {e}")
            return None

    def _limpar_e_converter_dados(self, dados_brutos: dict) -> dict:
        """
        Receives a dictionary of extracted data as strings and applies
        cleaning and conversion to numeric types.
        """
        dados_limpos = {}
        for chave, valor_str in dados_brutos.items():
            valor_limpo = valor_str
            try:
                # If the value contains '%', remove it, convert to float, and divide by 100
                if '%' in valor_str:
                    valor_limpo = float(valor_str.replace('%', '').replace('.', '').replace(',', '.')) / 100
                # If the value is a number (integer or decimal)
                elif re.match(r'^-?\d{1,3}(\.\d{3})*(,\d+)?$', valor_str):
                    valor_limpo = float(valor_str.replace('.', '').replace(',', '.'))
                # Other cases (like dates or plain text) remain as strings
            except (ValueError, TypeError):
                # If conversion fails, keep the original value or set it to None
                valor_limpo = None

            dados_limpos[chave] = valor_limpo

        return dados_limpos

    def _parsear_pagina_fii(self, html_content: str):
        """Helper method to extract data from a FII's page."""

        # Uses BeautifulSoup to parse the HTML
        soup = BeautifulSoup(html_content, 'lxml')

        # Creates the final data structure
        dados_fii = {}
        # Iterating through all tables
        for table in soup.find_all('table'):

            # Getting all table rows
            for row in table.find_all('tr'):
                # Getting the label elements
                labels = row.select('td[class*="label"]')
                # Getting the data elements
                data = row.select('td[class*="data"]')

                for label_cell, data_cell in zip(labels, data):
                    # Ensures both were found on the same line
                    if label_cell and data_cell:
                        # Cleans the text, removing spaces and the initial '?'
                        help_span = label_cell.find('span', class_='help')
                        if help_span:
                            help_span.decompose()  # Removes the entire <span> element

                        chave = label_cell.get_text(strip=True)
                        valor = data_cell.get_text(strip=True)

                        # Checks if the key is already in the dictionary
                        if chave in dados_fii:
                            chave = f"{chave}_2"

                        # Adds to our results dictionary
                        dados_fii[chave] = valor

        return dados_fii
