"""CSV parser for broker statements"""
import csv
import io
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CSVParser:
    """Parser for CSV broker statements with flexible column mapping"""
    
    # Common column name mappings for different brokers
    COLUMN_MAPPINGS = {
        "ticker": ["ticker", "symbol", "scrip", "instrument", "stock"],
        "isin": ["isin", "isincode", "isin_code"],
        "exchange": ["exchange", "bse", "nse", "market"],
        "qty": ["qty", "quantity", "shares", "units", "balance"],
        "avg_price": ["avg_price", "average_price", "cost_price", "purchase_price", "buy_price"],
        "valuation": ["valuation", "current_value", "market_value", "value"],
        "name": ["name", "company_name", "security_name", "scrip_name"],
    }
    
    def __init__(self, custom_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize CSV parser with optional custom column mapping.
        
        Args:
            custom_mapping: Dict mapping standard fields to CSV column names
                           e.g., {"ticker": "Symbol", "qty": "Quantity"}
        """
        self.custom_mapping = custom_mapping or {}
    
    def _normalize_column_name(self, col_name: str) -> str:
        """Normalize column name to lowercase and strip whitespace"""
        return col_name.lower().strip()
    
    def _find_column_index(self, headers: List[str], possible_names: List[str]) -> Optional[int]:
        """Find column index by matching against possible names"""
        normalized_headers = [self._normalize_column_name(h) for h in headers]
        
        for name in possible_names:
            normalized_name = self._normalize_column_name(name)
            if normalized_name in normalized_headers:
                return normalized_headers.index(normalized_name)
        
        return None
    
    def _build_column_map(self, headers: List[str]) -> Dict[str, int]:
        """Build mapping from standard fields to column indices"""
        column_map = {}
        
        for standard_field, possible_names in self.COLUMN_MAPPINGS.items():
            # Check custom mapping first
            if standard_field in self.custom_mapping:
                custom_col = self.custom_mapping[standard_field]
                idx = self._find_column_index(headers, [custom_col])
                if idx is not None:
                    column_map[standard_field] = idx
                    continue
            
            # Try standard mappings
            idx = self._find_column_index(headers, possible_names)
            if idx is not None:
                column_map[standard_field] = idx
        
        return column_map
    
    def parse(self, csv_content: str) -> List[Dict[str, Any]]:
        """
        Parse CSV content and return list of holding records.
        
        Args:
            csv_content: CSV file content as string
            
        Returns:
            List of dictionaries with normalized holding data
        """
        records = []
        
        try:
            # Use StringIO to read CSV from string
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            headers = reader.fieldnames or []
            
            if not headers:
                raise ValueError("CSV file has no headers")
            
            # Build column mapping
            column_map = self._build_column_map(headers)
            
            if not column_map:
                raise ValueError("Could not map any standard columns from CSV headers")
            
            # Parse each row
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                try:
                    record = self._parse_row(row, column_map, row_num)
                    if record:
                        records.append(record)
                except Exception as e:
                    logger.warning(f"Error parsing row {row_num}: {e}")
                    continue
            
            return records
            
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            raise ValueError(f"Failed to parse CSV: {e}")
    
    def _parse_row(self, row: Dict[str, str], column_map: Dict[str, int], row_num: int) -> Optional[Dict[str, Any]]:
        """Parse a single CSV row into a holding record"""
        row_list = list(row.values())
        
        # Extract values using column map
        ticker = None
        if "ticker" in column_map:
            ticker = row_list[column_map["ticker"]].strip() if row_list[column_map["ticker"]] else None
        
        isin = None
        if "isin" in column_map:
            isin = row_list[column_map["isin"]].strip() if row_list[column_map["isin"]] else None
        
        exchange = None
        if "exchange" in column_map:
            exchange = row_list[column_map["exchange"]].strip().upper() if row_list[column_map["exchange"]] else None
        
        # Quantity is required
        if "qty" not in column_map:
            logger.warning(f"Row {row_num}: No quantity column found, skipping")
            return None
        
        try:
            qty_str = row_list[column_map["qty"]].strip()
            qty = float(qty_str.replace(",", ""))
            if qty <= 0:
                return None  # Skip zero or negative quantities
        except (ValueError, IndexError):
            logger.warning(f"Row {row_num}: Invalid quantity value, skipping")
            return None
        
        # Optional fields
        avg_price = None
        if "avg_price" in column_map:
            try:
                price_str = row_list[column_map["avg_price"]].strip()
                if price_str:
                    avg_price = float(price_str.replace(",", ""))
            except (ValueError, IndexError):
                pass
        
        valuation = None
        if "valuation" in column_map:
            try:
                val_str = row_list[column_map["valuation"]].strip()
                if val_str:
                    valuation = float(val_str.replace(",", ""))
            except (ValueError, IndexError):
                pass
        
        # Name for reference
        name = None
        if "name" in column_map:
            name = row_list[column_map["name"]].strip() if row_list[column_map["name"]] else None
        
        # At least ticker or isin must be present
        if not ticker and not isin:
            logger.warning(f"Row {row_num}: No ticker or ISIN found, skipping")
            return None
        
        return {
            "ticker": ticker,
            "isin": isin,
            "exchange": exchange,
            "qty": qty,
            "avg_price": avg_price,
            "valuation": valuation,
            "name": name,
        }
    
    @staticmethod
    def generate_statement_hash(csv_content: str, account_id: int) -> str:
        """Generate hash for statement idempotency"""
        content_hash = hashlib.sha256(csv_content.encode()).hexdigest()
        return f"{account_id}:{content_hash}"

