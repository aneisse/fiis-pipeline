import pytest
from fiiscraper import Scraper
from fiiscraper.models.fii import FII

@pytest.mark.vcr # Marcador para rodar testes que dependem de conexão com a internet
def test_listar_todos_fiis_retorna_lista_de_objetos_fii():
    """
    Testa a função principal de listagem de FIIs.

    Este é um "teste de integração", pois ele acessa a internet de verdade.
    Ele verifica três coisas cruciais:
    1. O método retorna uma lista.
    2. A lista não está vazia.
    3. Os itens dentro da lista são do tipo correto (objetos da classe FII).
    """
    # 1. Setup
    scraper = Scraper()

    # 2. Execução
    resultado = scraper.listar_todos_fiis()

    # 3. Verificação (Asserts)
    assert isinstance(resultado, list), "O método deveria retornar uma lista."
    assert len(resultado) > 100, "A lista de FIIs retornada está muito pequena ou vazia."
    assert isinstance(resultado[0], FII), "Os itens da lista deveriam ser objetos da classe FII."
    print(f"\nTeste de listagem passou! Encontrados {len(resultado)} FIIs. Amostra: {resultado[0]}")

@pytest.mark.vcr # Marcador para rodar testes que dependem de conexão com a internet
def test_buscar_indicadores_dia_com_sucesso():
    """
    Testa se o scraper consegue buscar e parsear os indicadores de um FII específico.
    
    Verifica se:
    1. O método retorna um objeto da classe FII.
    2. O ticker do objeto retornado está correto.
    3. Atributos chave (como P/VP) foram populados (não são None).
    """
    # 1. Setup
    scraper = Scraper()
    ticker_teste = "MXRF11"

    # 2. Execução
    fii_resultante = scraper.buscar_indicadores_dia(ticker_teste)

    # 3. Verificação (Asserts)
    assert isinstance(fii_resultante, FII), "O método deveria retornar um objeto FII."
    assert fii_resultante.ticker == ticker_teste, "O ticker no objeto retornado está incorreto."
    assert fii_resultante.p_vp is not None, "O atributo P/VP não foi populado."
    assert fii_resultante.div_yield is not None, "O atributo Dividend Yield não foi populado."
    assert fii_resultante.receita_12_meses is not None, "O atributo Receita 12m (contextual) não foi populado."
    print(f"\nTeste de indicadores para {ticker_teste} passou! P/VP encontrado: {fii_resultante.p_vp}")

@pytest.mark.vcr
def test_buscar_indicadores_dia_com_ticker_invalido():
    """
    Testa se o scraper lida corretamente com um ticker que não existe no Fundamentus.
    Ele deve retornar None e não levantar uma exceção.
    """
    # 1. Setup
    scraper = Scraper()
    ticker_invalido = "XXXX11"

    # 2. Execução
    resultado = scraper.buscar_indicadores_dia(ticker_invalido)

    # 3. Verificação (Assert)
    assert resultado is None, "Para um ticker inválido, o método deveria retornar None."

@pytest.mark.vcr
def test_buscar_historico_precos_com_ticker_invalido():
    """
    Testa se o scraper lida corretamente com um ticker que não existe no yfinance.
    Ele deve retornar uma lista vazia.
    """
    # 1. Setup
    scraper = Scraper()
    ticker_invalido = "YYYY11"

    # 2. Execução
    resultado = scraper.buscar_historico_precos(ticker_invalido)

    # 3. Verificação (Asserts)
    assert isinstance(resultado, list), "O método deveria sempre retornar uma lista."
    assert len(resultado) == 0, "Para um ticker inválido, a lista retornada deveria estar vazia."
