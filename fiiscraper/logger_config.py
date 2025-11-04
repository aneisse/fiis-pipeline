import logging
import sys

def setup_logging(level=logging.INFO):
    """
    Configures the logging system for the project.
    """
    # Defines the format of log messages
    log_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )

    # Configures a "handler" to send messages to the console
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(log_format)

    # Gets the root logger and adds our handler to it
    logger = logging.getLogger()
    logger.setLevel(level)

    # Evita adicionar handlers duplicados se a função for chamada mais de uma vez
    if not logger.handlers:
        logger.addHandler(handler)
