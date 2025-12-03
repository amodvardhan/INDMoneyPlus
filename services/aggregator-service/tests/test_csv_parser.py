"""Tests for CSV parser"""
import pytest
from app.core.csv_parser import CSVParser


def test_csv_parser_standard_format():
    """Test CSV parser with standard column names"""
    csv_content = """Ticker,ISIN,Exchange,Quantity,Avg Price,Current Value
RELIANCE,INE002A01018,NSE,100,2500.50,255000.00
TCS,INE467B01029,NSE,50,3500.75,175037.50"""
    
    parser = CSVParser()
    records = parser.parse(csv_content)
    
    assert len(records) == 2
    assert records[0]["ticker"] == "RELIANCE"
    assert records[0]["isin"] == "INE002A01018"
    assert records[0]["exchange"] == "NSE"
    assert records[0]["qty"] == 100.0
    assert records[0]["avg_price"] == 2500.50
    assert records[0]["valuation"] == 255000.00


def test_csv_parser_alternate_format():
    """Test CSV parser with alternate column names"""
    csv_content = """Symbol,ISIN Code,Market,Shares,Cost Price,Market Value
AAPL,US0378331005,NASDAQ,25,150.00,3750.00"""
    
    parser = CSVParser()
    records = parser.parse(csv_content)
    
    assert len(records) == 1
    assert records[0]["ticker"] == "AAPL"
    assert records[0]["isin"] == "US0378331005"
    assert records[0]["exchange"] == "NASDAQ"
    assert records[0]["qty"] == 25.0
    assert records[0]["avg_price"] == 150.00


def test_csv_parser_custom_mapping():
    """Test CSV parser with custom column mapping"""
    csv_content = """Stock,Code,Bourse,Units,Price,Value
RELIANCE,INE002A01018,NSE,100,2500.50,255000.00"""
    
    custom_mapping = {
        "ticker": "Stock",
        "isin": "Code",
        "exchange": "Bourse",
        "qty": "Units",
        "avg_price": "Price",
        "valuation": "Value"
    }
    
    parser = CSVParser(custom_mapping=custom_mapping)
    records = parser.parse(csv_content)
    
    assert len(records) == 1
    assert records[0]["ticker"] == "RELIANCE"


def test_csv_parser_statement_hash():
    """Test statement hash generation"""
    csv_content = "test content"
    account_id = 1
    
    hash1 = CSVParser.generate_statement_hash(csv_content, account_id)
    hash2 = CSVParser.generate_statement_hash(csv_content, account_id)
    
    assert hash1 == hash2
    assert hash1.startswith("1:")


def test_csv_parser_invalid_csv():
    """Test CSV parser with invalid CSV"""
    csv_content = "not a valid csv"
    
    parser = CSVParser()
    with pytest.raises(ValueError):
        parser.parse(csv_content)

