import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import logging
import pandas as pd
import io  # Necessário para o buffer em memória
import io  # Required for the in-memory buffer

# Logging configuration to see informational and error messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def upload_df_to_s3(df: pd.DataFrame, bucket_name: str, s3_filename: str) -> bool:
    """
    Converts a pandas DataFrame to Parquet in memory and uploads it to S3.

    This is the optimized approach that avoids saving temporary files to disk.

    Args:
        df (pd.DataFrame): The DataFrame to be uploaded.
        bucket_name (str): The name of the destination S3 bucket.
        s3_filename (str): The name (path) the file will have in S3.

    Returns:
        bool: True if the upload was successful, False otherwise.
    """
    # Creates an S3 client. Boto3 will automatically look for credentials
    # in your environment (configured via 'aws configure' or an IAM Role on Lambda).
    s3_client = boto3.client('s3')

    logging.info(
        f"Starting in-memory DataFrame upload to "
        f"'s3://{bucket_name}/{s3_filename}'..."
    )

    try:
        # Creates an in-memory bytes buffer (a virtual "dispatch box")
        buffer_jsonl = io.StringIO()

        # Writes the DataFrame to the buffer in Parquet format
        df.to_json(buffer_jsonl, orient='records',  lines=True, force_ascii=False)

        # "Rewinds" the buffer to the beginning before reading it for the upload
        buffer_jsonl.seek(0)

        # Uses put_object to send the buffer's content (the bytes)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_filename,
            Body=buffer_jsonl.getvalue().encode('utf-8')
        )

        logging.info("Upload successful!")
        return True
    except NoCredentialsError:
        logging.error("Error: AWS credentials not found.")
        return False
    except ClientError as e:
        # Handles specific AWS API errors, like "Bucket Not Found"
        logging.error(f"An AWS error occurred: {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during the upload: {e}")
        return False
