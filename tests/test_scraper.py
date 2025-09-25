import pytest
import pandas as pd
from fiiscraper import Scraper
from fiiscraper.models.fii import FII


# --- Testes para Métodos de Scraping de Indicadores ---

@pytest.mark.vcr
def test_listar_todos_fiis_retorna_lista_de_objetos_fii():
    """Testa a função principal de listagem de FIIs."""
    scraper = Scraper()
    resultado = scraper.listar_todos_fiis()
    assert isinstance(resultado, list)
    assert len(resultado) > 100
    assert isinstance(resultado[0], FII)


@pytest.mark.vcr
def test_buscar_indicadores_dia_com_sucesso():
    """Testa se o scraper consegue buscar e parsear os indicadores de um FII específico."""
    scraper = Scraper()
    ticker_teste = "MXRF11"
    fii_resultante = scraper.buscar_indicadores_dia(ticker_teste)
    assert isinstance(fii_resultante, FII)
    assert fii_resultante.ticker == ticker_teste
    assert fii_resultante.p_vp is not None
    assert fii_resultante.receita_12_meses is not None


@pytest.mark.vcr
def test_buscar_indicadores_dia_com_ticker_invalido():
    """Testa se o scraper lida corretamente com um ticker que não existe no Fundamentus."""
    scraper = Scraper()
    ticker_invalido = "XXXX11"
    resultado = scraper.buscar_indicadores_dia(ticker_invalido)
    assert resultado is None, "Para um ticker inválido, buscar_indicadores_dia deveria retornar None."


# --- Testes para o Novo Método de Busca de Preços em Lote ---

@pytest.mark.vcr
def test_buscar_precos_em_lote_com_sucesso():
    """Testa o caminho feliz do download em lote com múltiplos tickers válidos."""
    scraper = Scraper()
    tickers_validos = ["MXRF11", "HGLG11"]
    
    resultado = scraper.buscar_precos_em_lote(tickers_validos)

    assert isinstance(resultado, pd.DataFrame), "O método deve sempre retornar um DataFrame."
    assert not resultado.empty, "O DataFrame não deveria estar vazio para tickers válidos."
    assert len(resultado) == len(tickers_validos), "Deveria haver uma linha por ticker válido."
    assert all(item in resultado['ticker'].tolist() for item in tickers_validos), "Nem todos os tickers solicitados foram retornados."
    assert 'close' in resultado.columns, "A coluna 'close' é esperada no resultado."


@pytest.mark.vcr
def test_buscar_precos_em_lote_com_ticker_unico_valido():
    """Testa o edge case de fazer o download em lote com apenas um ticker."""
    scraper = Scraper()
    ticker_valido = ["KNRI11"]
    
    resultado = scraper.buscar_precos_em_lote(ticker_valido)

    assert isinstance(resultado, pd.DataFrame)
    assert not resultado.empty
    assert len(resultado) == 1
    assert resultado['ticker'].iloc[0] == "KNRI11"


@pytest.mark.vcr
def test_buscar_precos_em_lote_com_ticker_invalido():
    """Testa se o método retorna um DataFrame vazio para um ticker que não existe."""
    scraper = Scraper()
    ticker_invalido = ["XXXX11"]

    resultado = scraper.buscar_precos_em_lote(ticker_invalido)
    
    assert isinstance(resultado, pd.DataFrame), "O método deve sempre retornar um DataFrame, mesmo para erros."
    assert resultado.empty, "O DataFrame deveria estar vazio para um ticker inválido."


@pytest.mark.vcr
def test_buscar_precos_em_lote_com_tickers_mistos():
    """Testa se o método lida corretamente com uma lista de tickers válidos e inválidos."""
    scraper = Scraper()
    tickers_mistos = ["MXRF11", "YYYY11", "VISC11"] # YYYY11 é inválido

    resultado = scraper.buscar_precos_em_lote(tickers_mistos)

    assert isinstance(resultado, pd.DataFrame)
    assert not resultado.empty
    assert len(resultado) == 2, "Deveria retornar dados apenas para os 2 tickers válidos."
    assert "MXRF11" in resultado['ticker'].tolist()
    assert "VISC11" in resultado['ticker'].tolist()
    assert "YYYY11" not in resultado['ticker'].tolist(), "Tickers inválidos não deveriam estar no resultado."