import os
import polars as pl
from backend.etl.pipeline import run_etl_job

if __name__ == "__main__":

    REAL_DATA_PATH = r"C:\Projects\selcom-financial-data-platform\data\raw\data.csv"
    
    #  database URI (pointing to  running Docker container)
    DB_URI = "postgresql://postgres:postgres@localhost:5432/selcom_db"
    
    print("="*70)
    print(" Paysim DATA PIPELINE VALIDATION RUN")
    print("="*70)
    
    # Check if the file actually exists
    if not os.path.exists(REAL_DATA_PATH):
        print(f" Error: File not found at path:\n   {REAL_DATA_PATH}")
        print("\nPlease verify the path spelling or place the CSV in the directory.")
    else:
        # Sneak peek the data size first using Polars
        metadata = pl.scan_csv(REAL_DATA_PATH)
        print(f" Targeted Dataset: '{os.path.basename(REAL_DATA_PATH)}'")
        print(f" Path: {REAL_DATA_PATH}")
        print(" Firing Polars ETL engine...")
        print("-"*70)
        
        try:
            # 3. Fire the pipeline on your real physical data!
            run_etl_job(source_path=REAL_DATA_PATH, db_uri=DB_URI)
            print("-"*70)
            print(" Real data successfully processed, validated, and bulk-loaded!")
            
        except Exception as e:
            print("-"*70)
            print(f"Pipeline Execution Failed: {str(e)}")
            print("\nTip: Check if the raw data column names match the schema expected by 'DataValidator'!")
            
    print("="*70)