import pytest
import pandas as pd
from fiiscraper import Scraper
from fiiscraper.models.fii import FII


# --- Tests for Indicator Scraping Methods ---

@pytest.mark.vcr
def test_listar_todos_fiis_retorna_lista_de_objetos_fii():
    """Tests the main FII listing function."""
    scraper = Scraper()
    resultado = scraper.listar_todos_fiis()
    assert isinstance(resultado, list)
    assert len(resultado) > 100
    assert isinstance(resultado[0], FII)


@pytest.mark.vcr
def test_buscar_indicadores_dia_com_sucesso():
    """Tests if the scraper can fetch and parse the indicators for a specific FII."""
    scraper = Scraper()
    ticker_teste = "MXRF11"
    fii_resultante = scraper.buscar_indicadores_dia(ticker_teste)
    assert isinstance(fii_resultante, FII)
    assert fii_resultante.ticker == ticker_teste
    assert fii_resultante.p_vp is not None
    assert fii_resultante.receita_12_meses is not None


@pytest.mark.vcr
def test_buscar_indicadores_dia_com_ticker_invalido():
    """Tests if the scraper correctly handles a ticker that does not exist on Fundamentus."""
    scraper = Scraper()
    ticker_invalido = "XXXX11"
    resultado = scraper.buscar_indicadores_dia(ticker_invalido)
    assert resultado is None, "For an invalid ticker, buscar_indicadores_dia should return None."


# --- Tests for the New Batch Price Fetching Method ---

@pytest.mark.vcr
def test_buscar_precos_em_lote_com_sucesso():
    """Tests the happy path of the batch download with multiple valid tickers."""
    scraper = Scraper()
    tickers_validos = ["MXRF11", "HGLG11"]
    
    resultado = scraper.buscar_precos_em_lote(tickers_validos)

    assert isinstance(resultado, pd.DataFrame), "The method should always return a DataFrame."
    assert not resultado.empty, "The DataFrame should not be empty for valid tickers."
    assert len(resultado) == len(tickers_validos), "There should be one row per valid ticker."
    assert all(item in resultado['ticker'].tolist() for item in tickers_validos), "Not all requested tickers were returned."
    assert 'close' in resultado.columns, "The 'close' column is expected in the result."


@pytest.mark.vcr
def test_buscar_precos_em_lote_com_ticker_unico_valido():
    """Tests the edge case of batch downloading with only a single ticker."""
    scraper = Scraper()
    ticker_valido = ["KNRI11"]
    
    resultado = scraper.buscar_precos_em_lote(ticker_valido)

    assert isinstance(resultado, pd.DataFrame)
    assert not resultado.empty
    assert len(resultado) == 1
    assert resultado['ticker'].iloc[0] == "KNRI11"


@pytest.mark.vcr
def test_buscar_precos_em_lote_com_ticker_invalido():
    """Tests if the method returns an empty DataFrame for a ticker that does not exist."""
    scraper = Scraper()
    ticker_invalido = ["XXXX11"]

    resultado = scraper.buscar_precos_em_lote(ticker_invalido)
    
    assert isinstance(resultado, pd.DataFrame), "The method should always return a DataFrame, even for errors."
    assert resultado.empty, "The DataFrame should be empty for an invalid ticker."


@pytest.mark.vcr
def test_buscar_precos_em_lote_com_tickers_mistos():
    """Tests if the method correctly handles a list of valid and invalid tickers."""
    scraper = Scraper()
    tickers_mistos = ["MXRF11", "YYYY11", "VISC11"] # YYYY11 is invalid

    resultado = scraper.buscar_precos_em_lote(tickers_mistos)

    assert isinstance(resultado, pd.DataFrame)
    assert not resultado.empty
    assert len(resultado) == 2, "It should return data only for the 2 valid tickers."
    assert "MXRF11" in resultado['ticker'].tolist()
    assert "VISC11" in resultado['ticker'].tolist()
    assert "YYYY11" not in resultado['ticker'].tolist(), "Invalid tickers should not be in the result."