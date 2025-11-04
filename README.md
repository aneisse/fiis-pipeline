# FIIs Data Pipeline

## Overview

This project is a data pipeline designed to collect, process, and store data on Brazilian Real Estate Investment Funds (Fundos de Investimento Imobiliário - FIIs) listed on the B3 stock exchange. It automates the process of scraping data from public sources, transforming it into a usable format, and storing it in a data lake for analysis.

## Estrutura do Projeto

The project is structured as follows:

```bash
fiis-pipeline/
├── fiiscraper/
│   ├── scraper.py          # Core scraping logic
│   ├── aws_uploader.py     # S3 JSONL upload utility
│   ├── models/fii.py       # FII data class
│   └── logger_config.py    # Logging configuration
│
├── lambda_ingestion/
│   └── lambda_handler.py   # AWS Lambda entry point (handler)
│
├── infra/
│   └── main.tf             # Terraform (IaC) definition for all resources
│
├── tests/
│   ├── test_scraper.py         # Tests for scraper.py (uses VCR)
│   ├── test_aws_uploader.py    # Tests for uploader (uses moto)
│   └── test_lambda_handler.py  # Integration tests for the lambda (uses pytest-mock)
│
├── main.py                 # Local script to run the pipeline manually
├── requirements.txt        # Project dependencies
└── README.md               # This file
```

## Components

### Scraper (`fiiscraper/scraper.py`)
*   Fetches FII data from web sources using libraries like `requests` and `Beautiful Soup`.
*   Extracts key information such as daily indicators and price history.

### AWS Uploader (`fiiscraper/aws_uploader.py`)
*   Uploads processed data to an S3 bucket in Parquet format.
*   Handles authentication and error handling for S3 interactions.

### Lambda Function (`lambda_ingestion/lambda_handler.py`)
*   An AWS Lambda function that automates the data scraping and uploading process.
*   Orchestrates the execution of the scraper and uploader components.
*   Configured to run on a schedule using AWS CloudWatch Events.

### Infrastructure as Code (`infra/main.tf`)
*   Terraform configuration to provision AWS resources:
    *   S3 bucket for storing raw data.
    *   IAM role with necessary permissions for the Lambda function.
    *   CloudWatch event rule to trigger the Lambda function daily.
    *   Lambda function with environment variables for configuration.

## Prerequisites

Before running this project, you'll need to have the following:

*   **Python 3.10+**: Ensure you have Python 3.10 or a compatible version installed.
*   **AWS Account**: You'll need an active AWS account to deploy the infrastructure.
*   **Terraform**: Install Terraform CLI to provision infrastructure.
*   **AWS CLI**: Configure AWS CLI with the necessary credentials.

## Setup

### 1. Clone the Repository

```bash
git clone <repository_url>
cd fiis-pipeline
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Linux/macOS
venv\Scripts\activate.bat  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure AWS Credentials

Make sure your AWS CLI is configured with the necessary credentials to access your AWS account.

### 5. Terraform Setup

*   Navigate to the `infra` directory:

    ```bash
    cd infra
    ```
*   Initialize Terraform:

    ```bash
    terraform init
    ```
*   Apply the Terraform configuration:

    ```bash
    terraform apply
    ```

### 6. Build Lambda Package

*   Run the `build_lambda_package.ps1` script to package the Lambda function.

    ```powershell
    .\scripts\build_lambda_package.ps1
    ```

### 7. Upload Lambda Package to S3

*   Upload the generated `lambda_package.zip` to the S3 bucket created by Terraform, under the path `lambda_code/lambda_package.zip`.

## Running the Pipeline

### Locally

To run the pipeline locally, execute the `main.py` script:

```bash
python main.py
```

Make sure to set the `BUCKET_S3` environment variable to the name of your S3 bucket.

### AWS Lambda

The pipeline is designed to run automatically as an AWS Lambda function triggered by a CloudWatch event. Once deployed, it will run daily at the specified time.

## License

This project is licensed under the [MIT License](LICENSE).

## Future improvements

*   Solve the issue where executing the app in AWS without a proxy will result in **403 Forbidden** from the Fundamentus website.
*   **Databricks Integration**: Ingest the raw JSONL data from S3 into a Databricks Delta Lake.
*   **Data Transformation (Medallion)**: Implement a Medallion architecture (Bronze, Silver, Gold) using Delta Live Tables (DLT) to create clean, aggregated analytical tables.
