#!/usr/bin/env python3
"""
Data Cleaning & Transformation Tool
A comprehensive tool for cleaning, transforming, and analyzing datasets using pandas.
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Union, Callable, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

import pandas as pd
import numpy as np
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CleaningReport:
    """Report of data cleaning operations."""
    input_rows: int = 0
    output_rows: int = 0
    duplicates_removed: int = 0
    missing_values_filled: Dict[str, int] = field(default_factory=dict)
    type_conversions: Dict[str, str] = field(default_factory=dict)
    outliers_detected: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def retention_rate(self) -> float:
        if self.input_rows == 0:
            return 0.0
        return (self.output_rows / self.input_rows) * 100


class DataCleaner:
    """
    Main data cleaning class with comprehensive transformation capabilities.
    """
    
    def __init__(self, source: Union[str, pd.DataFrame], **kwargs):
        """
        Initialize the data cleaner.
        
        Args:
            source: File path or pandas DataFrame
            **kwargs: Additional arguments for file loading
        """
        self.report = CleaningReport()
        self.transformations: List[str] = []
        
        if isinstance(source, str):
            self.df = self._load_file(source, **kwargs)
        else:
            self.df = source.copy()
        
        self.original_df = self.df.copy()
        self.report.input_rows = len(self.df)
        
        logger.info(f"Loaded data: {len(self.df)} rows × {len(self.df.columns)} columns")
    
    def _load_file(self, filepath: str, **kwargs) -> pd.DataFrame:
        """Load data from various file formats."""
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        ext = path.suffix.lower()
        
        if ext == '.csv':
            # Try to detect encoding
            encodings = ['utf-8', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    return pd.read_csv(filepath, encoding=encoding, **kwargs)
                except UnicodeDecodeError:
                    continue
            return pd.read_csv(filepath, encoding='utf-8', errors='ignore', **kwargs)
        
        elif ext in ['.xlsx', '.xls']:
            return pd.read_excel(filepath, **kwargs)
        
        elif ext == '.json':
            return pd.read_json(filepath, **kwargs)
        
        elif ext == '.parquet':
            return pd.read_parquet(filepath, **kwargs)
        
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def remove_duplicates(self, subset: Optional[List[str]] = None, 
                          keep: str = 'first') -> 'DataCleaner':
        """
        Remove duplicate rows.
        
        Args:
            subset: Columns to consider for duplicates
            keep: Which duplicate to keep ('first', 'last', False)
        """
        before_count = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset, keep=keep)
        removed = before_count - len(self.df)
        
        self.report.duplicates_removed = removed
        self.transformations.append(f"Removed {removed} duplicate rows")
        
        if removed > 0:
            logger.info(f"Removed {removed} duplicate rows")
        
        return self
    
    def handle_missing(self, strategy: Union[str, Dict[str, str]] = 'drop',
                       fill_value: Any = None) -> 'DataCleaner':
        """
        Handle missing values in the dataset.
        
        Args:
            strategy: 'drop', 'mean', 'median', 'mode', 'fill', or dict of column strategies
            fill_value: Value to use when strategy is 'fill'
        """
        if isinstance(strategy, dict):
            for col, strat in strategy.items():
                if col not in self.df.columns:
                    logger.warning(f"Column '{col}' not found")
                    continue
                
                missing_count = self.df[col].isna().sum()
                
                if strat == 'drop':
                    self.df = self.df.dropna(subset=[col])
                elif strat == 'mean' and self.df[col].dtype in ['int64', 'float64']:
                    self.df[col] = self.df[col].fillna(self.df[col].mean())
                elif strat == 'median' and self.df[col].dtype in ['int64', 'float64']:
                    self.df[col] = self.df[col].fillna(self.df[col].median())
                elif strat == 'mode':
                    self.df[col] = self.df[col].fillna(self.df[col].mode()[0])
                elif strat == 'fill':
                    self.df[col] = self.df[col].fillna(fill_value)
                elif strat == 'ffill':
                    self.df[col] = self.df[col].fillna(method='ffill')
                elif strat == 'bfill':
                    self.df[col] = self.df[col].fillna(method='bfill')
                
                self.report.missing_values_filled[col] = missing_count
                logger.info(f"Filled {missing_count} missing values in '{col}' using '{strat}'")
        
        else:
            missing_before = self.df.isna().sum().sum()
            
            if strategy == 'drop':
                self.df = self.df.dropna()
            elif strategy == 'fill':
                self.df = self.df.fillna(fill_value)
            elif strategy == 'ffill':
                self.df = self.df.fillna(method='ffill')
            elif strategy == 'bfill':
                self.df = self.df.fillna(method='bfill')
            
            self.transformations.append(f"Handled missing values using '{strategy}'")
            logger.info(f"Handled {missing_before} missing values")
        
        return self
    
    def convert_types(self, type_map: Dict[str, str]) -> 'DataCleaner':
        """
        Convert column data types.
        
        Args:
            type_map: Dictionary mapping column names to target types
                     ('int', 'float', 'str', 'datetime', 'bool', 'category')
        """
        for col, dtype in type_map.items():
            if col not in self.df.columns:
                logger.warning(f"Column '{col}' not found")
                continue
            
            try:
                if dtype == 'datetime':
                    self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                elif dtype == 'category':
                    self.df[col] = self.df[col].astype('category')
                elif dtype == 'int':
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce').astype('Int64')
                elif dtype == 'float':
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                else:
                    self.df[col] = self.df[col].astype(dtype)
                
                self.report.type_conversions[col] = dtype
                logger.info(f"Converted '{col}' to {dtype}")
                
            except Exception as e:
                logger.error(f"Failed to convert '{col}' to {dtype}: {e}")
        
        return self
    
    def standardize_columns(self, case: str = 'snake') -> 'DataCleaner':
        """
        Standardize column names.
        
        Args:
            case: 'snake', 'camel', 'pascal', or 'lower'
        """
        def to_snake(name: str) -> str:
            # Replace spaces and special chars with underscore
            name = re.sub(r'[^\w\s]', '', name)
            name = re.sub(r'\s+', '_', name.strip())
            # Insert underscore before capital letters
            name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
            return name
        
        def to_camel(name: str) -> str:
            parts = to_snake(name).split('_')
            return parts[0] + ''.join(p.capitalize() for p in parts[1:])
        
        def to_pascal(name: str) -> str:
            parts = to_snake(name).split('_')
            return ''.join(p.capitalize() for p in parts)
        
        converters = {
            'snake': to_snake,
            'camel': to_camel,
            'pascal': to_pascal,
            'lower': lambda x: x.lower().replace(' ', '_'),
        }
        
        if case not in converters:
            raise ValueError(f"Unknown case: {case}")
        
        old_columns = list(self.df.columns)
        self.df.columns = [converters[case](col) for col in self.df.columns]
        
        self.transformations.append(f"Standardized column names to {case}_case")
        logger.info(f"Renamed columns: {dict(zip(old_columns, self.df.columns))}")
        
        return self
    
    def clean_text(self, columns: Optional[List[str]] = None,
                   strip_whitespace: bool = True,
                   normalize_case: Optional[str] = None,
                   remove_extra_spaces: bool = True) -> 'DataCleaner':
        """
        Clean text columns.
        
        Args:
            columns: List of columns to clean (None = all object columns)
            strip_whitespace: Remove leading/trailing whitespace
            normalize_case: 'lower', 'upper', 'title', or None
            remove_extra_spaces: Replace multiple spaces with single space
        """
        if columns is None:
            columns = self.df.select_dtypes(include=['object']).columns.tolist()
        
        for col in columns:
            if col not in self.df.columns:
                continue
            
            if strip_whitespace:
                self.df[col] = self.df[col].str.strip()
            
            if remove_extra_spaces:
                self.df[col] = self.df[col].str.replace(r'\s+', ' ', regex=True)
            
            if normalize_case == 'lower':
                self.df[col] = self.df[col].str.lower()
            elif normalize_case == 'upper':
                self.df[col] = self.df[col].str.upper()
            elif normalize_case == 'title':
                self.df[col] = self.df[col].str.title()
        
        self.transformations.append(f"Cleaned text in {len(columns)} columns")
        return self
    
    def remove_outliers(self, columns: List[str], method: str = 'iqr',
                        threshold: float = 1.5) -> 'DataCleaner':
        """
        Remove or flag outliers in numeric columns.
        
        Args:
            columns: Columns to check for outliers
            method: 'iqr' (interquartile range) or 'zscore'
            threshold: Threshold for outlier detection
        """
        outlier_count = 0
        
        for col in columns:
            if col not in self.df.columns:
                continue
            
            if not pd.api.types.is_numeric_dtype(self.df[col]):
                logger.warning(f"Column '{col}' is not numeric, skipping outlier detection")
                continue
            
            if method == 'iqr':
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - threshold * IQR
                upper = Q3 + threshold * IQR
                mask = (self.df[col] >= lower) & (self.df[col] <= upper)
            
            elif method == 'zscore':
                z_scores = np.abs((self.df[col] - self.df[col].mean()) / self.df[col].std())
                mask = z_scores < threshold
            
            col_outliers = (~mask).sum()
            outlier_count += col_outliers
            
            # Remove outliers
            self.df = self.df[mask]
            
            logger.info(f"Removed {col_outliers} outliers from '{col}'")
        
        self.report.outliers_detected = outlier_count
        self.transformations.append(f"Removed {outlier_count} outliers using {method}")
        
        return self
    
    def validate_emails(self, column: str, remove_invalid: bool = False) -> 'DataCleaner':
        """
        Validate email addresses in a column.
        
        Args:
            column: Column containing email addresses
            remove_invalid: Remove rows with invalid emails
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        valid_mask = self.df[column].str.match(email_pattern, na=False)
        invalid_count = (~valid_mask).sum()
        
        logger.info(f"Found {invalid_count} invalid emails in '{column}'")
        
        if remove_invalid:
            self.df = self.df[valid_mask]
            self.transformations.append(f"Removed {invalid_count} invalid emails")
        else:
            self.df[f'{column}_valid'] = valid_mask
            self.transformations.append(f"Flagged {invalid_count} invalid emails")
        
        return self
    
    def extract_dateparts(self, column: str, 
                          parts: List[str] = None) -> 'DataCleaner':
        """
        Extract date components into separate columns.
        
        Args:
            column: Datetime column
            parts: List of parts to extract ('year', 'month', 'day', 'weekday', 'hour')
        """
        if parts is None:
            parts = ['year', 'month', 'day']
        
        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(self.df[column]):
            self.df[column] = pd.to_datetime(self.df[column], errors='coerce')
        
        for part in parts:
            new_col = f"{column}_{part}"
            
            if part == 'year':
                self.df[new_col] = self.df[column].dt.year
            elif part == 'month':
                self.df[new_col] = self.df[column].dt.month
            elif part == 'day':
                self.df[new_col] = self.df[column].dt.day
            elif part == 'weekday':
                self.df[new_col] = self.df[column].dt.dayofweek
            elif part == 'hour':
                self.df[new_col] = self.df[column].dt.hour
            elif part == 'quarter':
                self.df[new_col] = self.df[column].dt.quarter
        
        self.transformations.append(f"Extracted date parts from '{column}'")
        return self
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the dataset."""
        return {
            'rows': len(self.df),
            'columns': len(self.df.columns),
            'column_types': self.df.dtypes.to_dict(),
            'missing_values': self.df.isna().sum().to_dict(),
            'memory_usage_mb': self.df.memory_usage(deep=True).sum() / 1024 / 1024
        }
    
    def export(self, filepath: str, **kwargs) -> 'DataCleaner':
        """
        Export cleaned data to file.
        
        Args:
            filepath: Output file path
            **kwargs: Additional arguments for export functions
        """
        path = Path(filepath)
        ext = path.suffix.lower()
        
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if ext == '.csv':
            self.df.to_csv(filepath, index=False, **kwargs)
        elif ext in ['.xlsx', '.xls']:
            self.df.to_excel(filepath, index=False, **kwargs)
        elif ext == '.json':
            self.df.to_json(filepath, orient='records', **kwargs)
        elif ext == '.parquet':
            self.df.to_parquet(filepath, **kwargs)
        else:
            raise ValueError(f"Unsupported export format: {ext}")
        
        self.report.output_rows = len(self.df)
        logger.info(f"Exported {len(self.df)} rows to {filepath}")
        
        return self
    
    def generate_report(self) -> str:
        """Generate a text report of cleaning operations."""
        lines = [
            "📊 Data Cleaning Report",
            "=" * 50,
            f"Input Rows: {self.report.input_rows}",
            f"Output Rows: {self.report.output_rows}",
            f"Retention Rate: {self.report.retention_rate:.1f}%",
            "",
            "Transformations Applied:",
        ]
        
        for i, trans in enumerate(self.transformations, 1):
            lines.append(f"  {i}. {trans}")
        
        lines.extend([
            "",
            f"Duplicates Removed: {self.report.duplicates_removed}",
            f"Outliers Detected: {self.report.outliers_detected}",
        ])
        
        if self.report.type_conversions:
            lines.extend(["", "Type Conversions:"])
            for col, dtype in self.report.type_conversions.items():
                lines.append(f"  - {col}: → {dtype}")
        
        return "\n".join(lines)


def main():
    """Demo the data cleaner with sample operations."""
    print("=" * 60)
    print("🧹 Data Cleaning Tool Demo")
    print("=" * 60)
    
    # Create sample dirty data
    sample_data = pd.DataFrame({
        'Customer Name': ['  john doe  ', 'JANE SMITH', 'bob johnson', 'john doe', None],
        'Email': ['john@example.com', 'invalid-email', 'bob@test.com', 'john@example.com', 'alice@domain.com'],
        'Purchase_Date': ['2024-01-15', '2024/02/20', 'invalid', '2024-01-15', '2024-03-10'],
        'Amount': ['100.50', '250.00', '5000.00', '100.50', None],  # 5000 is outlier
        'Quantity': ['2', '5', '1', '2', '3']
    })
    
    # Save sample data
    sample_data.to_csv('/home/node/.openclaw/workspace/portfolio/data-cleaning-tool/sample_dirty_data.csv', index=False)
    print("\n📁 Created sample dirty data")
    print(f"   Rows: {len(sample_data)}")
    print(f"   Columns: {list(sample_data.columns)}")
    
    # Initialize cleaner
    cleaner = DataCleaner('/home/node/.openclaw/workspace/portfolio/data-cleaning-tool/sample_dirty_data.csv')
    
    # Apply transformations
    print("\n🔄 Running cleaning pipeline...\n")
    
    (cleaner
        .remove_duplicates()
        .standardize_columns(case='snake')
        .clean_text(columns=['customer_name'], normalize_case='title', strip_whitespace=True)
        .validate_emails('email', remove_invalid=True)
        .convert_types({
            'purchase_date': 'datetime',
            'amount': 'float',
            'quantity': 'int'
        })
        .remove_outliers(['amount'], method='iqr')
        .extract_dateparts('purchase_date', parts=['year', 'month', 'day', 'weekday'])
    )
    
    # Export results
    cleaner.export('/home/node/.openclaw/workspace/portfolio/data-cleaning-tool/clean_output.csv')
    
    # Print report
    print("\n" + cleaner.generate_report())
    
    print("\n✅ Cleaning complete! Check clean_output.csv for results.")


if __name__ == "__main__":
    main()
