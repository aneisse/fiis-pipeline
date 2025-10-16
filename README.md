# FIIs Data Pipeline

This project is a Python-based data pipeline designed to scrape, process, and store financial data for Brazilian Real Estate Investment Trusts (FIIs). It gathers information from public web sources and prepares it for analysis and storage.

## Features

*   **Comprehensive FII Listing**: Automatically scrapes a complete list of all FIIs available on the [Fundamentus](https://www.fundamentus.com.br/fii_imoveis.php) website.
*   **Daily Indicator Scraping**: For each FII, it fetches detailed daily indicators, including:
    *   Valuation metrics (P/VP, Market Value)
    *   Yield indicators (Dividend Yield, FFO Yield)
    *   Price history (52-week Min/Max, daily/monthly variation)
    *   Portfolio details (Number of properties, vacancy rate, etc.)
*   **Historical Price Fetching**: Downloads recent daily closing prices and volume data from Yahoo Finance in an efficient batch process.
*   **Data Consolidation**: The pipeline is structured to consolidate the scraped data into structured formats (Pandas DataFrames).
*   **Cloud Integration (WIP)**: Includes placeholders and structure for uploading the processed data to an AWS S3 bucket.

## Data Sources

1.  **Fundamentus**: Used for obtaining the master list of FIIs and their detailed fundamental indicators.
2.  **Yahoo Finance (via `yfinance` library)**: Used for fetching historical daily price and volume data.

## Project Structure

```
fiis-pipeline/
├── fiiscraper/
│   ├── __init__.py
│   ├── scraper.py          # Contains the Scraper class for all data extraction logic.
│   ├── models/
│   │   └── fii.py          # Data model for a FII object.
│   ├── aws_uploader.py     # Handles uploading data to AWS S3.
│   └── logger_config.py    # Configures application-wide logging.
│
├── main.py                 # Main entry point to execute the data pipeline.
├── requirements.txt        # Project dependencies.
└── README.md               # This file.
```

### Key Components

*   `main.py`: The orchestrator. It initializes the scraper, runs the data collection steps in sequence, and calls the uploader.
*   `fiiscraper/scraper.py`: The core of the project. The `Scraper` class contains methods to:
    *   `listar_todos_fiis()`: Get all FII tickers from Fundamentus.
    *   `buscar_indicadores_dia()`: Scrape the details page of a single FII on Fundamentus.
    *   `buscar_precos_em_lote()`: Download price data for multiple tickers from Yahoo Finance.

## How to Run

### 1. Prerequisites

*   Python 3.8+
*   An AWS account with an S3 bucket and configured credentials (if you intend to use the S3 upload functionality).

### 2. Installation

Clone the repository and install the required dependencies.

```bash
git clone <your-repository-url>
cd fiis-pipeline
pip install -r requirements.txt
```

*(Note: A `requirements.txt` file would need to be created containing libraries like `pandas`, `requests`, `beautifulsoup4`, `lxml`, `yfinance`, and `boto3`)*

### 3. Configuration

Before running, open `main.py` and set the name of your S3 bucket:

```python
# c:\Users\41755\Desktop\fiis-pipeline\main.py

# --- CONFIGURAÇÃO ---
BUCKET_S3 = 'your-s3-bucket-name'
```

### 4. Execution

Run the main script from the project's root directory:

```bash
python main.py
```

The script will log its progress to the console, indicating which steps are being executed (listing FIIs, fetching indicators, fetching prices, and uploading to S3).

## Future Improvements

- Implement the data upload logic for S3 in `main.py`.
- Add more robust error handling and retry mechanisms for network requests.
- Store data in an efficient file format like Parquet.
- Set up the pipeline to run on a schedule (e.g., using GitHub Actions or AWS Lambda).