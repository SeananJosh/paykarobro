import pandas as pd
from io import StringIO
from datetime import datetime
from decimal import Decimal
from typing import List, Dict

class DataIngestionService:
    """
    Handles parsing and ingestion of financial data (CSV/JSON).
    """
    
    @staticmethod
    def parse_expenses_csv(csv_content: str) -> List[Dict]:
        """
        Parses a CSV with columns: vendor, amount, due_date, category
        """
        df = pd.read_csv(StringIO(csv_content))
        
        # Basic validation/normalization
        required_cols = ['vendor', 'amount', 'due_date']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
                
        results = []
        for _, row in df.iterrows():
            results.append({
                "vendor_name": str(row['vendor']),
                "amount": Decimal(str(row['amount'])),
                "due_date": datetime.strptime(str(row['due_date']), '%Y-%m-%d').date(),
                "category": str(row.get('category', 'Miscellaneous'))
            })
        return results

    @staticmethod
    def parse_bank_statement_csv(csv_content: str) -> List[Dict]:
        """
        Parses bank statements for cash flow history.
        Columns: date, description, amount, balance
        """
        df = pd.read_csv(StringIO(csv_content))
        results = []
        for _, row in df.iterrows():
            results.append({
                "transaction_date": datetime.strptime(str(row['date']), '%Y-%m-%d').date(),
                "description": str(row['description']),
                "amount": Decimal(str(row['amount'])),
                "balance_after": Decimal(str(row['balance'])),
                "category": str(row.get('category', 'General'))
            })
        return results
