import os
import polars as pl

from backend.etl.logger import logger
from backend.etl.quality import DataValidator
from backend.etl.transformer import DataTransformer
from backend.etl.loader import PostgresLoader


def run_etl_job(source_path: str, db_uri: str):
    """
    Executes the complete end-to-end ETL orchestration flow:
    1. EXTRACT: Read raw CSV into memory using Polars' multi-threaded reader.
    2. VALIDATE: Run schema and anomaly validation checks from quality.py.
    3. TRANSFORM: Clean, rename, and add derived features using Polars expressions.
    4. LOAD: Streams the clean dataframe into PostgreSQL with COPY/UPSERT logic.
    """
    logger.info("Initializing ETL pipeline execution...")

    
    # 1. EXTRACT PHASE
    
    if not os.path.exists(source_path):
        logger.error(f"Extraction failed: Source CSV file not found at '{source_path}'")
        return

    try:
        logger.info(f"Extracting data from: {source_path}")
        df_raw = pl.read_csv(source_path)
        logger.info(f"Extraction successful! Loaded {df_raw.height} records.")
    except Exception as e:
        logger.critical(f"Pipeline crashed during EXTRACT phase: {e}")
        return

    
    # 2. VALIDATION PHASE (Indentation Fixed)
    
    try:
        validation_report = DataValidator.validate(df_raw)
        if not validation_report["valid"]:
            logger.error("Pipeline run aborted: Critical schema or structural errors detected.")
            return
        
        # EXTRACT THE SANITIZED DATAFRAME
        df_clean = validation_report["sanitized_df"]
    except Exception as e:
        logger.critical(f"Pipeline crashed during VALIDATE phase: {e}")
        return

   
    # 3. TRANSFORMATION PHASE
   
    try:
        # Pass the CLEAN dataset instead of df_raw!
        df_transformed = DataTransformer.transform(df_clean)
    except Exception as e:
        logger.critical(f"Pipeline crashed during TRANSFORM phase: {e}")
        return

    
    # 4. LOAD PHASE

    try:
        loader = PostgresLoader(connection_uri=db_uri)
        loader.load_data(df_transformed)
        logger.info("ETL Pipeline finalized successfully! 🚀")
        
    except Exception as e:
        logger.critical(f"Pipeline crashed during LOAD phase: {e}")
        return


if __name__ == "__main__":
    SOURCE_CSV = "data/transactions.csv"
    
    # Dynamically fetch DATABASE_URL from environment, falling back to a local default
    DB_URI = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@postgres:5432/selcom_db"
    )
    
    run_etl_job(source_path=SOURCE_CSV, db_uri=DB_URI)