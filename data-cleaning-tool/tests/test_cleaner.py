import pandas as pd
import numpy as np
import pytest
from datetime import datetime

from clean_data import DataCleaner, CleaningReport


class TestDataCleaner:
    """Tests for the DataCleaner class."""
    
    def test_load_csv(self, tmp_path):
        """Test loading CSV file."""
        # Create test CSV
        test_file = tmp_path / "test.csv"
        test_file.write_text("name,age\nAlice,30\nBob,25")
        
        cleaner = DataCleaner(str(test_file))
        assert len(cleaner.df) == 2
        assert list(cleaner.df.columns) == ['name', 'age']
    
    def test_remove_duplicates(self):
        """Test duplicate removal."""
        df = pd.DataFrame({
            'A': [1, 2, 2, 3],
            'B': ['x', 'y', 'y', 'z']
        })
        cleaner = DataCleaner(df)
        cleaner.remove_duplicates()
        
        assert len(cleaner.df) == 3
        assert cleaner.report.duplicates_removed == 1
    
    def test_handle_missing_drop(self):
        """Test dropping rows with missing values."""
        df = pd.DataFrame({
            'A': [1, 2, None, 4],
            'B': ['x', None, 'z', 'w']
        })
        cleaner = DataCleaner(df)
        cleaner.handle_missing(strategy='drop')
        
        assert len(cleaner.df) == 1  # Only row 4 has no missing values
    
    def test_handle_missing_fill(self):
        """Test filling missing values."""
        df = pd.DataFrame({
            'A': [1, 2, None, 4],
        })
        cleaner = DataCleaner(df)
        cleaner.handle_missing(strategy='fill', fill_value=0)
        
        assert cleaner.df['A'].isna().sum() == 0
        assert cleaner.df['A'].iloc[2] == 0
    
    def test_convert_types(self):
        """Test data type conversion."""
        df = pd.DataFrame({
            'price': ['10.5', '20.3', '30.1'],
            'count': ['1', '2', '3']
        })
        cleaner = DataCleaner(df)
        cleaner.convert_types({'price': 'float', 'count': 'int'})
        
        assert cleaner.df['price'].dtype == 'float64'
        assert cleaner.df['count'].dtype == 'int64'
    
    def test_standardize_columns(self):
        """Test column name standardization."""
        df = pd.DataFrame({
            'Customer Name': [1],
            'Email Address': [2],
            'PurchaseDate': [3]
        })
        cleaner = DataCleaner(df)
        cleaner.standardize_columns(case='snake')
        
        expected = ['customer_name', 'email_address', 'purchase_date']
        assert list(cleaner.df.columns) == expected
    
    def test_clean_text(self):
        """Test text cleaning."""
        df = pd.DataFrame({
            'name': ['  JOHN DOE  ', '  jane  smith  ']
        })
        cleaner = DataCleaner(df)
        cleaner.clean_text(normalize_case='title', remove_extra_spaces=True)
        
        assert cleaner.df['name'].iloc[0] == 'John Doe'
        assert cleaner.df['name'].iloc[1] == 'Jane Smith'
    
    def test_validate_emails(self):
        """Test email validation."""
        df = pd.DataFrame({
            'email': ['valid@example.com', 'invalid-email', 'also@valid.com']
        })
        cleaner = DataCleaner(df)
        cleaner.validate_emails('email', remove_invalid=False)
        
        assert 'email_valid' in cleaner.df.columns
        assert cleaner.df['email_valid'].sum() == 2
    
    def test_remove_outliers_iqr(self):
        """Test outlier removal using IQR method."""
        df = pd.DataFrame({
            'value': [10, 12, 11, 13, 12, 1000]  # 1000 is outlier
        })
        cleaner = DataCleaner(df)
        cleaner.remove_outliers(['value'], method='iqr')
        
        assert len(cleaner.df) == 5  # Outlier removed
        assert 1000 not in cleaner.df['value'].values
    
    def test_extract_dateparts(self):
        """Test date part extraction."""
        df = pd.DataFrame({
            'date': ['2024-01-15', '2024-06-20']
        })
        cleaner = DataCleaner(df)
        cleaner.extract_dateparts('date', parts=['year', 'month', 'day'])
        
        assert 'date_year' in cleaner.df.columns
        assert 'date_month' in cleaner.df.columns
        assert cleaner.df['date_year'].iloc[0] == 2024
        assert cleaner.df['date_month'].iloc[0] == 1
    
    def test_export_csv(self, tmp_path):
        """Test CSV export."""
        df = pd.DataFrame({'A': [1, 2], 'B': ['x', 'y']})
        cleaner = DataCleaner(df)
        
        output_file = tmp_path / "output.csv"
        cleaner.export(str(output_file))
        
        assert output_file.exists()
        
        # Verify content
        exported = pd.read_csv(output_file)
        assert len(exported) == 2


class TestCleaningReport:
    """Tests for the CleaningReport class."""
    
    def test_retention_rate(self):
        """Test retention rate calculation."""
        report = CleaningReport(input_rows=100, output_rows=75)
        assert report.retention_rate == 75.0
    
    def test_retention_rate_zero_input(self):
        """Test retention rate with zero input."""
        report = CleaningReport(input_rows=0, output_rows=0)
        assert report.retention_rate == 0.0
