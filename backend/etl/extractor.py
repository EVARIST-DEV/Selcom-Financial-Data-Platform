# backend/etl/extractor.py
import os
import polars as pl
from typing import List, Optional
from etl.utils import logger

class FinancialDataExtractor:
    """Discovers and lazily loads transaction source files using Polars."""
    
    def __init__(self, raw_data_dir: str):
        self.raw_data_dir = raw_data_dir
        if not os.path.exists(self.raw_data_dir):
            os.makedirs(self.raw_data_dir, exist_ok=True)
            logger.warning(f"Raw data directory did not exist. Created at: {self.raw_data_dir}")

    def discover_csv_files(self) -> List[str]:
        """Scans the directory for CSV data inputs."""
        files = [
            os.path.join(self.raw_data_dir, f)
            for f in os.listdir(self.raw_data_dir)
            if f.endswith(".csv")
        ]
        logger.info(f"Discovered {len(files)} target CSV file(s) for extraction.")
        return sorted(files)

    def extract_lazy(self, file_path: str) -> Optional[pl.LazyFrame]:
        """
        Creates a Polars LazyFrame from a CSV target.
        Enables streaming execution, predicate pushdowns, and schema inference.
        """
        if not os.path.exists(file_path):
            logger.error(f"Target extraction file not found: {file_path}")
            return None
        
        try:
            logger.info(f"Lazily scanning: {file_path}")
            # Infer schema automatically, setting low-memory optimization parameters
            lf = pl.scan_csv(
                file_path,
                infer_schema_length=10000,
                rechunk=True,
                ignore_errors=False
            )
            return lf
        except Exception as e:
            logger.exception(f"Failed to extract lazy query plan for {file_path}: {e}")
            return None