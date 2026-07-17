import polars as pl
from backend.etl.logger import logger


class DataValidator:
    """
    Handles inline Data Quality (DQ) validation, schema enforcement,
    and row-level sanitization on raw Polars DataFrames.
    """

    @staticmethod
    def validate(df: pl.DataFrame) -> dict:
        """
        Runs assertion checks on the raw DataFrame, filters out corrupted rows,
        and returns a validation report along with the sanitized DataFrame.
        """
        logger.info("Running Data Quality (DQ) checks on raw dataset...")
        
        report = {
            "valid": True,
            "total_rows": df.height,
            "sanitized_df": df,  # Will hold the clean data
            "failures": []
        }

        # 1. Check for Empty Dataset
        if df.height == 0:
            report["valid"] = False
            report["failures"].append("Dataset is empty.")
            logger.error("DQ Fail: The extracted CSV contains 0 rows.")
            return report

        # 2. Check for Mandatory Columns (Schema Consistency)
        required_columns = ["step", "type", "amount", "nameOrig", "nameDest"]
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            report["valid"] = False
            report["failures"].append(f"Missing required columns: {missing_cols}")
            logger.error(f"DQ Fail: Schema mismatch. Missing columns: {missing_cols}")
            return report

        # 3. Handle Null Values in nameOrig (Drop corrupted rows)
        null_count = df.filter(pl.col("nameOrig").is_null()).height
        if null_count > 0:
            logger.warning(f"DQ Alert: Found {null_count} records with missing origin account IDs. Filtering them out...")
            report["sanitized_df"] = report["sanitized_df"].filter(pl.col("nameOrig").is_not_null())

        # 4. Handle Invalid Amounts <= 0 (Quarantine/Filter out)
        if "amount" in df.columns:
            invalid_df = df.filter(pl.col("amount") <= 0)
            invalid_count = invalid_df.height
            
            if invalid_count > 0:
                logger.warning(f"DQ Alert: Found {invalid_count} transactions with amounts <= 0 (e.g., test or failed transactions). Filtering them out...")
                
                # Filter our sanitized DataFrame to only keep positive transaction amounts
                report["sanitized_df"] = report["sanitized_df"].filter(pl.col("amount") > 0)
                
                # Log a small preview of what got quarantined for investigation
                logger.info(f"Sample quarantined transactions: {invalid_df.select(['nameOrig', 'nameDest', 'amount']).head(3)}")

        # Final Evaluation Summary
        logger.success(
            f"Data Quality checks complete! "
            f"Filtered out {df.height - report['sanitized_df'].height} bad rows. "
            f"Proceeding with {report['sanitized_df'].height} clean records."
        )

        return report