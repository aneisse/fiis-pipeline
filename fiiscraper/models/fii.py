class FII:
    def __init__(self, ticker):

        # FII base attributes
        self.ticker = ticker
        self.nome = None

        # Management Indicators
        self.mandato = None
        self.segmento = None
        self.tipo_gestao = None

        # Price Indicators
        self.cotacao = None
        self.data_ult_cotacao = None
        self.min_52_semanas = None
        self.max_52_semanas = None
        self.volume_medio_2meses = None
        self.valor_mercado = None
        self.numero_cotas = None
        self.data_ult_relatorio_gerencial = None
        self.data_ult_info_trimestral = None
        self.var_dia = None
        self.var_mes = None
        self.var_30_dias = None
        self.var_12_meses = None

        # Yield Indicators
        self.ffo_yield = None
        self.ffo_cota = None
        self.div_yield = None
        self.div_cota = None
        self.p_vp = None
        self.vp_cota = None

        # Revenue Indicators
        self.receita_12_meses = None
        self.venda_ativos_12_meses = None
        self.ffo_12_meses = None
        self.rendimento_distribuido_12_meses = None
        self.receita_3_meses = None
        self.venda_ativos_3_meses = None
        self.ffo_3_meses = None
        self.rendimento_distribuido_3_meses = None

        # Equity Indicators
        self.ativos = None
        self.patrimonio_liquido = None

        # Real Estate Indicators
        self.qtd_imoveis = None
        self.qtd_unidades = None
        self.imoveis_pl = None
        self.metros_quadrados = None
        self.aluguel_metro_quadrado = None
        self.preco_metro_quadrado = None
        self.cap_rate = None
        self.vacancia_media = None

        # Indicator to mark if the FII was found on yfinance
        self.tem_dados_yfinance = False

    def __repr__(self):
        # This method defines how the object will be displayed when printed
        return f"FII(ticker='{self.ticker}')"
