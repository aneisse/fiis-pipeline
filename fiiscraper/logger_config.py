import logging
import sys

def setup_logging(level=logging.INFO):
    """
    Configura o sistema de logging para o projeto.
    """
    # Define o formato das mensagens de log
    log_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )

    # Configura um "handler" para enviar as mensagens para o terminal
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(log_format)

    # Obtém o logger raiz e adiciona o nosso handler a ele
    logger = logging.getLogger()
    logger.setLevel(level)

    # Evita adicionar handlers duplicados se a função for chamada mais de uma vez
    if not logger.handlers:
        logger.addHandler(handler)
