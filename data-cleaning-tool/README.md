# Data Cleaning & Transformation Tool

A powerful Python tool for cleaning, transforming, and analyzing messy datasets using pandas. Perfect for preparing data for analysis, machine learning, or reporting.

## Features

- 🧹 Clean messy data (handle nulls, duplicates, outliers)
- 🔄 Transform data formats (date parsing, type conversion)
- 📊 Generate data quality reports
- 📝 Export to multiple formats (CSV, Excel, JSON, Parquet)
- 🎨 Standardize text and categorical data
- 📈 Automated profiling and statistics
- 🔍 Pattern detection and validation

## Setup Instructions

### Prerequisites

- Python 3.8+
- pandas, numpy, openpyxl

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/data-cleaning-tool.git
cd data-cleaning-tool
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
# Basic cleaning
python clean_data.py input.csv --output clean_data.csv

# Full pipeline with all transformations
python clean_data.py data.xlsx --output processed.parquet --config config.yaml

# Generate report only
python clean_data.py input.csv --report data_report.html
```

### As a Library

```python
from data_cleaner import DataCleaner

# Initialize cleaner
cleaner = DataCleaner('input.csv')

# Apply transformations
cleaner.remove_duplicates()
cleaner.handle_missing(strategy='mean')
cleaner.standardize_columns()
cleaner.convert_types({'date': 'datetime', 'price': 'float'})

# Export results
cleaner.export('clean_output.xlsx')
```

## Project Structure

```
data-cleaning-tool/
├── clean_data.py         # CLI entry point
├── data_cleaner.py       # Main cleaning class
├── transformers.py       # Data transformation functions
├── validators.py         # Data validation rules
├── profiler.py           # Data profiling and analysis
├── reporters.py          # Report generation
├── config.yaml          # Default configuration
├── sample_data/         # Example datasets
│   ├── dirty_sales.csv
│   └── customer_data.xlsx
├── tests/
│   ├── test_cleaner.py
│   └── test_transformers.py
├── requirements.txt
└── README.md
```

## Sample Output

### Data Quality Report

```
📊 Data Quality Report - dirty_sales.csv
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 File Information
   ├─ Rows: 10,542
   ├─ Columns: 12
   ├─ File Size: 2.3 MB
   └─ Memory Usage: 4.1 MB

🔍 Missing Values Analysis
   Column              | Missing   | % Missing  | Suggested Action
   ───────────────────────────────────────────────────────────────
   customer_email      | 234       | 2.2%       | Remove rows
   phone_number        | 1,892     | 17.9%      | Impute/Remove
   purchase_date       | 45        | 0.4%       | Interpolate
   discount_code       | 8,234     | 78.1%      | Keep as null

🔍 Duplicate Detection
   ├─ Exact Duplicates: 127 rows (1.2%)
   └─ Fuzzy Duplicates: 43 potential matches

📊 Column Statistics

   purchase_amount (Numeric)
   ├─ Mean: $145.32
   ├─ Median: $89.50
   ├─ Std Dev: $203.45
   ├─ Min: $0.99
   ├─ Max: $9,999.99 ⚠️ Potential outlier
   └─ Nulls: 12 (0.1%)

   customer_name (Text)
   ├─ Unique Values: 9,847
   ├─ Empty Strings: 23
   ├─ Max Length: 128 chars
   └─ Pattern Issues: 156 (special characters)

   purchase_date (DateTime)
   ├─ Range: 2020-01-01 to 2024-01-15
   ├─ Invalid Dates: 23
   ├─ Future Dates: 2 ⚠️
   └─ Format Consistency: 94%
```

### Cleaning Pipeline Output

```
🧹 Data Cleaning Pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Load Data
   ✓ Loaded 10,542 rows × 12 columns
   ✓ Detected encoding: UTF-8

Step 2: Remove Duplicates
   ✓ Removed 127 exact duplicates
   ✓ Flagged 43 fuzzy matches for review
   → Remaining: 10,415 rows

Step 3: Handle Missing Values
   ├─ customer_email: Dropped 234 rows (no recovery possible)
   ├─ phone_number: Imputed using customer_id lookup
   ├─ purchase_date: Interpolated from order_id sequence
   └→ Remaining: 10,181 rows

Step 4: Data Type Conversion
   ├─ purchase_date: string → datetime64[ns]
   ├─ purchase_amount: string → float64
   ├─ quantity: string → int64
   └─ zip_code: int64 → string (preserves leading zeros)

Step 5: Standardize Text Fields
   ├─ customer_name: Title case applied
   ├─ email: Lowercase + validation
   ├─ phone: Standardized to E.164 format
   └─ Removed 156 rows with invalid email patterns

Step 6: Outlier Detection
   ├─ purchase_amount: Flagged 23 outliers (>3σ)
   ├─ quantity: Capped at 99 (business rule)
   └→ Winsorization applied

Step 7: Validate Data
   ├─ Email format: 99.8% valid
   ├─ Phone format: 97.2% valid
   ├─ Date range: Valid
   └→ 42 rows failed validation, exported to errors.csv

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Final Results
   Input Rows:     10,542
   Output Rows:    10,139 (96.2% retention)
   Time Elapsed:   3.45 seconds
   Memory Peak:    12.3 MB

💾 Export Complete
   ├─ clean_data.parquet (2.1 MB)
   ├─ clean_data.csv (1.8 MB)
   └─ cleaning_report.html (245 KB)
```

### Transformation Log

```
🔄 Transformation Log
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[2024-01-15 10:30:15] INFO: Starting pipeline
[2024-01-15 10:30:16] INFO: Loaded dirty_sales.csv
[2024-01-15 10:30:18] WARNING: Found 127 duplicate rows at indices [45, 127, 289, ...]
[2024-01-15 10:30:19] INFO: Removed duplicates
[2024-01-15 10:30:21] WARNING: phone_number column has 1,892 nulls (17.9%)
[2024-01-15 10:30:23] INFO: Imputed 1,543 phone numbers via lookup
[2024-01-15 10:30:25] ERROR: 349 phone numbers unrecoverable
[2024-01-15 10:30:27] INFO: Standardized text columns
[2024-01-15 10:30:28] WARNING: Detected 23 outliers in purchase_amount
[2024-01-15 10:30:30] INFO: Applied winsorization
[2024-01-15 10:30:32] INFO: Pipeline complete - 96.2% data retained
```

## Configuration

Create a `config.yaml` file:

```yaml
cleaning:
  remove_duplicates: true
  duplicate_columns: ['customer_email', 'phone_number']
  
missing_values:
  customer_email:
    strategy: drop
  phone_number:
    strategy: impute
    method: lookup
  purchase_amount:
    strategy: fill
    value: 0

type_conversions:
  purchase_date: datetime
  purchase_amount: float
  quantity: int
  zip_code: string

text_standardization:
  customer_name:
    case: title
    trim: true
    remove_extra_spaces: true
  email:
    case: lower
    validate_format: true

outliers:
  purchase_amount:
    method: winsorize
    lower_percentile: 0.01
    upper_percentile: 0.99

validation:
  email_regex: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
  phone_regex: '^\+?[1-9]\d{1,14}$'
```

## Available Transformations

### Data Cleaning
- `remove_duplicates()` - Remove exact and fuzzy duplicates
- `handle_missing(strategy)` - Handle null values
- `remove_outliers(method)` - Detect and handle outliers
- `fix_data_types()` - Auto-detect and convert types

### Text Processing
- `standardize_case(case)` - Title, lower, upper case
- `clean_whitespace()` - Trim, normalize spaces
- `remove_special_chars(keep)` - Strip unwanted characters
- `normalize_text()` - Unicode normalization

### Date Processing
- `parse_dates(format)` - Flexible date parsing
- `standardize_timezone(tz)` - Convert timezones
- `extract_dateparts()` - Create year/month/day columns

### Validation
- `validate_email(column)` - Email format validation
- `validate_phone(column, country)` - Phone number validation
- `validate_range(column, min, max)` - Range checks
- `validate_regex(column, pattern)` - Custom regex patterns

## Example Use Cases

### Cleaning Customer Data

```python
from data_cleaner import DataCleaner

cleaner = DataCleaner('customers.csv')

# Clean and standardize
cleaner.standardize_columns()
cleaner.handle_missing({
    'email': 'drop',
    'phone': 'impute'
})

# Validate
cleaner.validate_email('email')
cleaner.validate_phone('phone', country='US')

# Export
cleaner.export('clean_customers.csv', index=False)
```

### Sales Data Pipeline

```python
# Process monthly sales data
cleaner = DataCleaner('sales_2024.xlsx', sheet_name='January')

# Transform
cleaner.convert_types({
    'date': 'datetime',
    'amount': 'float',
    'units': 'int'
})

cleaner.extract_dateparts('date', parts=['year', 'month', 'weekday'])
cleaner.calculate_column('revenue', 'amount * units')

# Aggregate
cleaner.groupby_aggregate(
    by=['region', 'product'],
    agg={'revenue': 'sum', 'units': 'sum'}
)

cleaner.export('monthly_summary.parquet')
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=data_cleaner tests/

# Run specific test file
pytest tests/test_transformers.py -v
```

## License

MIT License
