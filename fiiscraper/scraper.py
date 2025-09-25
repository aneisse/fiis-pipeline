# Import de pacotes
import requests
from bs4 import BeautifulSoup
from fiiscraper.models.fii import FII
import yfinance as yf
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import lxml


class Scraper:
    """
    Classe responsável pela coleta de dados de FIIs de diversas fontes.
    """
    def __init__(self):
        # Fonte da lista de FIIs disponíveis para scraping
        self.url_lista_fiis = "https://www.fundamentus.com.br/fii_imoveis.php"

        # URL base para obtenção do link de cada página
        self.url_base_fii = "https://www.fundamentus.com.br/detalhes.php"  # Ex: ?papel=MXRF11

        # URL de API para obtenção dos dados de preço histórico
        self.url_base_api_precos = "https://brapi.dev/api/quote/"  # Ex: MXRF11?range=3mo

        # Simulando um navegador real.
        # Muitos sites bloqueiam requisições sem cabeçalhos de navegadores
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/58.0.3029.110 Safari/537.36'
            )
        }

    # --- MÉTODOS PÚBLICOS ---

    def listar_todos_fiis(self):
        """
        Busca a lista de todos os FIIs listados no site Fundamentus.

        Returns:
            list[FII]: Uma lista de objetos da classe FII, cada um
                       inicializado com o ticker.
        """
        print("Iniciando busca pela lista de todos os FIIs no Fundamentus...")

        # Faz a requisição HTTP para obter o conteúdo da página
        response = self._buscar_html(self.url_lista_fiis)

        # Usa o BeautifulSoup para parsear (analisar) o HTML
        soup = BeautifulSoup(response.text, 'lxml')

        # Encontra a tabela que contém a lista de FIIs
        tabela = soup.find('table', {'id': 'tabelaFiiImoveis'})
        if not tabela:
            print("Tabela de FIIs não encontrada na página.")
            return []

        lista_de_fiis = []
        # Itera sobre todas as linhas (<tr>) do corpo da tabela (<tbody>)
        # O [1:] pula a primeira linha, que é o cabeçalho da tabela
        for linha in tabela.find('tbody').find_all('tr'):
            # Em cada linha, pega a primeira célula (<td>), que contém o ticker
            celulas = linha.find_all('td')
            if celulas:
                ticker = celulas[0].text.strip()

                # Cria o objeto FII e adiciona na nossa lista
                novo_fii = FII(ticker=ticker)
                lista_de_fiis.append(novo_fii)

        lista_de_fiis = list(set(lista_de_fiis))  # Remove duplicatas

        print(f"{len(lista_de_fiis)} FIIs encontrados.")
        return lista_de_fiis

    def buscar_indicadores_dia(self, ticker: str):
        """
        Busca os indicadores de um FII específico no Fundamentus.
        Retorna um objeto da classe FII.
        """
        print(f"Buscando indicadores para {ticker}...")
        # Construindo o URL de acordo com o site do Fundamentus
        url_fii = f"{self.url_base_fii}?papel={ticker}"

        # Faz a requisição HTTP para obter o conteúdo da página
        response = self._buscar_html(url_fii)
        if not response:
            return None

        # Aplica o método privado de parsing do HTML
        indicadores_fii = self._parsear_pagina_fii(response.text)
        if not indicadores_fii  or 'Cotação' not in indicadores_fii:
            print(f"  > Conteúdo principal não encontrado para {ticker}. Ticker provavelmente inválido.")
            return None

        # Popula os dados do FII
        fii = FII(ticker=ticker)
        # Dados gerais
        fii.nome = indicadores_fii.get('Nome')
        fii.mandato = indicadores_fii.get('Mandato')
        fii.segmento = indicadores_fii.get('Segmento')
        fii.tipo_gestao = indicadores_fii.get('Gestão')

        # Indicadores da Cotação
        fii.cotacao = indicadores_fii.get('Cotação')
        fii.data_ult_cotacao = indicadores_fii.get('Data últ cot')
        fii.min_52_semanas = indicadores_fii.get('Min 52 sem')
        fii.max_52_semanas = indicadores_fii.get('Max 52 sem')
        fii.volume_medio_2meses = indicadores_fii.get('Vol $ méd (2m)')
        fii.valor_mercado = indicadores_fii.get('Valor de mercado')
        fii.numero_cotas = indicadores_fii.get('Nro. Cotas')
        # fii.data_ult_relatorio_gerencial = indicadores_fii.get('')
        fii.data_ult_info_trimestral = indicadores_fii.get('Últ Info Trimestral')
        fii.var_dia = indicadores_fii.get('Dia')
        fii.var_mes = indicadores_fii.get('Mês')
        fii.var_30_dias = indicadores_fii.get('30 dias')
        fii.var_12_meses = indicadores_fii.get('12 meses')

        # Indicadores de Rendimento
        fii.ffo_yield = indicadores_fii.get('FFO Yield')
        fii.ffo_cota = indicadores_fii.get('FFO/Cota')
        fii.div_yield = indicadores_fii.get('FFO Yield')
        fii.div_cota = indicadores_fii.get('Dividendo/cota')
        fii.p_vp = indicadores_fii.get('P/VP')
        fii.vp_cota = indicadores_fii.get('VP/Cota')

        # indicadores de resultados
        fii.receita_12_meses = indicadores_fii.get('Receita')
        fii.venda_ativos_12_meses = indicadores_fii.get('Venda de ativos')
        fii.ffo_12_meses = indicadores_fii.get('FFO')
        fii.rendimento_distribuido_12_meses = indicadores_fii.get('Rend. Distribuído')
        fii.receita_3_meses = indicadores_fii.get('Receita_2')
        fii.venda_ativos_3_meses = indicadores_fii.get('Venda de ativos_2')
        fii.ffo_3_meses = indicadores_fii.get('FFO_2')
        fii.rendimento_distribuido_3_meses = indicadores_fii.get('Rend. Distribuído_2')

        # indicadores de patrimônio
        fii.ativos = indicadores_fii.get('Ativos')
        fii.patrimonio_liquido = indicadores_fii.get('Patrim Líquido')

        # indicadores de imóveis
        fii.qtd_imoveis = indicadores_fii.get('Qtd imóveis')
        fii.qtd_unidades = indicadores_fii.get('Qtd Unidades')
        fii.imoveis_pl = indicadores_fii.get('Imóveis/PL do FII')
        fii.metros_quadrados = indicadores_fii.get('Área (m2)')
        fii.aluguel_metro_quadrado = indicadores_fii.get('Aluguel/m2')
        fii.preco_metro_quadrado = indicadores_fii.get('Preço do m2')
        fii.cap_rate = indicadores_fii.get('Cap Rate')
        fii.vacancia_media = indicadores_fii.get('Vacância Média')

        return fii

    def buscar_precos_em_lote(self, tickers: list[str]) -> pd.DataFrame:
        """
        Busca o preço de fecho mais recente para uma lista de tickers de forma otimizada,
        fazendo um único download em lote.

        Args:
            tickers (list[str]): Uma lista de tickers de FIIs (ex: ['MXRF11', 'HGLG11']).

        Returns:
            pd.DataFrame: Um DataFrame contendo 'ticker', 'date', 'close' e 'volume'
                          para todos os tickers que foram encontrados. Retorna um
                          DataFrame vazio em caso de erro.
        """
        print(f"Buscando preços recentes em lote para {len(tickers)} tickers via yfinance...")
        if not tickers:
            return pd.DataFrame()

        try:
            # Adiciona o sufixo .SA a todos os tickers da lista
            tickers_sa = [f"{ticker}.SA" for ticker in tickers]

            # Faz o download em lote. yf.download é muito mais rápido para múltiplos tickers.
            # Pedimos 5 dias para garantir que apanhamos o último dia útil disponível.
            df_lote = yf.Tickers(tickers_sa).download(period="30d", progress=False, auto_adjust=False)
            
            if df_lote.empty:
                return pd.DataFrame()
            
            # Reestrutura os dados
            df_final = df_lote.stack(future_stack=True).reset_index()
            df_final

            # Renomeia as colunas para o nosso padrão
            df_final.columns = [col.lower() for col in df_final.columns]

            # Dropa valroes que não tem preço
            df_final = df_final.dropna(subset=['close'])

            # Pega apenas o dia mais recente para cada ticker
            df_final = df_final.loc[df_final.groupby('ticker')['date'].idxmax()]

            # Limpa o sufixo .SA dos tickers
            df_final['ticker'] = df_final['ticker'].str.replace('.SA', '', regex=False)
            
            # Formata a data
            df_final['date'] = df_final['date'].dt.strftime('%Y-%m-%d')
            
            print(f"  > Preços de {len(df_final)} tickers encontrados com sucesso.")
            return df_final

        except Exception as e:
            print(f"  > Ocorreu um erro ao buscar dados em lote no yfinance: {e}")
            return pd.DataFrame()

    # --- MÉTODOS PRIVADOS ---

    def _buscar_html(self, url: str):
        """Método auxiliar para fazer a requisição HTTP e retornar o HTML."""

        print(f" > Acessando URL: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()  # Lança um erro para status ruins (404, 500, etc.)
            return response
        except requests.RequestException as e:
            print(f"Erro ao acessar a URL: {e}")
            return None

    def _parsear_pagina_fii(self, html_content: str):
        """Método auxiliar para extrair os dados da página de um FII."""

        # Usa o BeautifulSoup para parsear (analisar) o HTML
        soup = BeautifulSoup(html_content, 'lxml')

        # Cria estrutura de dados final
        dados_fii = {}
        # Iterando em todas as tabelas
        for table in soup.find_all('table'):

            # Obtendo todas as linhas das tabelas
            for line in table.find_all('tr'):
                # Obtendo os elementos de label
                labels = line.select('td[class*="label"]')
                # Obtendo os elmentos de dados
                data = line.select('td[class*="data"]')

                for label_cell, data_cell in zip(labels, data):
                    # Garante que ambos foram encontrados na mesma linha
                    if label_cell and data_cell:
                        # Limpa o texto, removendo espaços e o '?' inicial
                        help_span = label_cell.find('span', class_='help')
                        if help_span:
                            help_span.decompose()  # Remove o elemento <span> inteiro

                        chave = label_cell.get_text(strip=True)
                        valor = data_cell.get_text(strip=True)

                        # Checa se a chave já está contida no DIC
                        if chave in dados_fii:
                            chave = f"{chave}_2"

                        # Adiciona ao nosso dicionário de resultados
                        dados_fii[chave] = valor

        return dados_fii
