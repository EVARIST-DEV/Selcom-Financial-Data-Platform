import os
import polars as pl
from backend.etl.pipeline import run_pipeline

def setup_mock_data():
    """
    Generates sample CSV records with keys required by quality.py 
    and structural variables mapped by transformer.py
    """
    os.makedirs("data", exist_ok=True)
    
    mock_data = {
        # Fields checked by DataValidator (quality.py)
        "transaction_id": ["TXN-001", "TXN-002", "TXN-003", "TXN-001"], # TXN-001 is duplicate to test UPSERT idempotency
        "amount": [250000.00, 1500.00, 45000.00, 250000.00], 
        "customer_id": ["CUST-101", "CUST-102", "CUST-103", "CUST-101"],
        "timestamp": ["2026-07-15 12:00:00", "2026-07-15 13:00:00", "2026-07-15 14:00:00", "2026-07-15 12:00:00"],
        
        # Fields handled by DataTransformer (transformer.py)
        "step": [12, 34, 58, 12], # Represents hours elapsed for calculation matrices
        "type": ["PAYMENT", "TRANSFER", "CASH_OUT", "PAYMENT"],
        "status": ["COMPLETED", "COMPLETED", "PENDING", "COMPLETED"],
        "nameOrig": ["CUST-101", "CUST-102", "CUST-103", "CUST-101"],
        "nameDest": ["MERCH-01", "CUST-205", "MERCH-02", "MERCH-01"],
        "oldbalanceOrg": [500000.00, 2000.00, 60000.00, 500000.00],
        "newbalanceOrig": [250000.00, 500.00, 15000.00, 250000.00],
        "oldbalanceDest": [0.00, 10000.00, 5000.00, 0.00],
        "newbalanceDest": [250000.00, 11500.00, 50000.00, 250000.00]
    }
    
    df = pl.DataFrame(mock_data)
    df.write_csv("data/transactions.csv")
    print("Test data setup complete: Created 'data/transactions.csv'")


if __name__ == "__main__":
    # 1. Setup sample input payload files
    setup_mock_data()
    
    # 2. Local database connection configurations
    DB_URI = "postgresql://postgres:postgres@localhost:5432/selcom_db"
    
    # 3. Fire local pipeline validation run
    print("\nExecuting isolated local ETL system test pipeline...")
    run_pipeline(source_path="data/transactions.csv", db_uri=DB_URI)