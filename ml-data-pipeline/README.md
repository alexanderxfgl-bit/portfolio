# ML Data Pipeline Framework

A modular, production-ready framework for building machine learning data pipelines. Extract, transform, validate, and deliver data for model training and inference — with built-in data quality checks, versioning, and observability.

## Features

- **Modular pipeline stages**: Extract → Transform → Validate → Load, fully composable
- **Data validation**: Schema validation, type checking, null detection, distribution drift alerts
- **Multiple data sources**: CSV, JSON, Parquet, SQL databases, S3/GCS, REST APIs
- **Incremental processing**: Track processed records, handle deduplication
- **Data versioning**: Automatic snapshot versioning of processed datasets
- **Observability**: Structured logging, timing metrics, error tracking, Slack alerts
- **Async execution**: Built on asyncio for concurrent stage execution

## Use Cases

- Preparing training data from messy production databases
- Building feature engineering pipelines
- ETL for ML model serving (batch predictions)
- Data quality monitoring and drift detection
- Aggregating data from multiple sources for analytics

## Tech Stack

Python 3.11+, pandas, pyarrow, sqlalchemy, pydantic, aiohttp, rich

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
python pipeline.py --config configs/example.yaml
```

## Example Pipeline

```yaml
name: customer-churn-training-data
description: Extract customer data, engineer features, validate, export for training

stages:
  - name: extract_customers
    type: sql
    source: postgresql://user:pass@localhost/customers_db
    query: |
      SELECT c.*, o.order_count, o.total_spent
      FROM customers c
      LEFT JOIN order_aggregates o ON c.id = o.customer_id
      WHERE c.created_at > '2024-01-01'

  - name: extract_transactions
    type: csv
    path: data/transactions_2024.csv
    chunk_size: 10000

  - name: merge_and_engineer
    type: transform
    operations:
      - merge:
          on: customer_id
          how: left
      - feature:
          name: days_since_last_order
          expr: "(now() - last_order_date).days"
      - feature:
          name: avg_order_value
          expr: "total_spent / order_count"
      - filter:
          condition: "order_count > 0"

  - name: validate
    type: validate
    checks:
      - no_nulls: ["customer_id", "email", "total_spent"]
      - range: {"total_spent": [0, 100000]}
      - unique: ["customer_id"]
      - distribution_drift:
          column: "avg_order_value"
          reference: data/previous_distribution.json

  - name: export
    type: parquet
    path: output/training_data_v{version}.parquet
    partition_by: [churn_label]
```

## Project Structure

```
ml-data-pipeline/
├── pipeline.py           # CLI pipeline runner
├── stages/
│   ├── extract.py        # Data extraction (SQL, CSV, JSON, API)
│   ├── transform.py      # Transformations and feature engineering
│   ├── validate.py       # Data quality validation
│   └── load.py           # Output to Parquet, CSV, database
├── core/
│   ├── config.py         # Pipeline YAML config parser
│   ├── state.py          # Pipeline state and checkpointing
│   └── metrics.py        # Timing, row counts, quality scores
├── configs/
│   └── example.yaml
├── requirements.txt
├── .env.example
├── README.md
└── tests/
    └── test_pipeline.py
```

## License

MIT
