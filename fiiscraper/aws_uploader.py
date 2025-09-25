import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import logging
import pandas as pd
import io  # Necessário para o buffer em memória

# Configuração de logging para vermos mensagens informativas e de erro
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def upload_df_para_s3(df: pd.DataFrame, nome_bucket: str, nome_arquivo_s3: str) -> bool:
    """
    Converte um DataFrame do pandas para Parquet em memória e faz o upload para o S3.

    Esta é a abordagem otimizada que evita salvar ficheiros temporários no disco.

    Args:
        df (pd.DataFrame): O DataFrame a ser enviado.
        nome_bucket (str): O nome do bucket S3 de destino.
        nome_arquivo_s3 (str): O nome (caminho) que o arquivo terá no S3.

    Returns:
        bool: True se o upload foi bem-sucedido, False caso contrário.
    """
    # Cria um cliente S3. O boto3 buscará as credenciais automaticamente
    # do seu ambiente (configuradas via 'aws configure' ou IAM Role no Lambda).
    s3_client = boto3.client('s3')

    logging.info(
        f"Iniciando upload de DataFrame em memória para "
        f"'s3://{nome_bucket}/{nome_arquivo_s3}'..."
    )

    try:
        # 1. Cria um buffer de bytes em memória (uma "caixa de despacho" virtual)
        buffer_parquet = io.BytesIO()

        # 2. Escreve o DataFrame no buffer em formato Parquet
        df.to_parquet(buffer_parquet, index=False)

        # 3. "Rebobina" o buffer para o início antes de o ler para o upload
        buffer_parquet.seek(0)

        # 4. Usa put_object para enviar o conteúdo do buffer (os bytes)
        s3_client.put_object(
            Bucket=nome_bucket,
            Key=nome_arquivo_s3,
            Body=buffer_parquet
        )

        logging.info("Upload realizado com sucesso!")
        return True
    except NoCredentialsError:
        logging.error("Erro: Credenciais da AWS não encontradas.")
        return False
    except ClientError as e:
        # Trata erros específicos da API da AWS, como "Bucket Not Found"
        logging.error(f"Um erro da AWS ocorreu: {e}")
        return False
    except Exception as e:
        logging.error(f"Um erro inesperado ocorreu durante o upload: {e}")
        return False
