import polars as pl
from backend.etl.logger import logger


class DataValidator:
    """
    Performs fast, multi-threaded data quality checks before transformation using Polars.
    """

    REQUIRED_COLUMNS = [
        "step",
        "type",
        "amount",
        "nameOrig",
        "oldbalanceOrg",
        "newbalanceOrig",
        "nameDest",
        "oldbalanceDest",
        "newbalanceDest",
        "isFraud",
        "isFlaggedFraud",
    ]

    VALID_TRANSACTION_TYPES = {
        "PAYMENT",
        "TRANSFER",
        "CASH_IN",
        "CASH_OUT",
        "DEBIT",
    }

    @classmethod
    def validate(cls, df: pl.DataFrame) -> dict:
        logger.info("Running Polars data validation...")

        missing_cols = [col for col in cls.REQUIRED_COLUMNS if col not in df.columns]

        rows = df.height
        cols = df.width
        
        # Parallel horizontal computation of missing values across all columns
        null_count = df.select(pl.all().is_null().sum()).sum_horizontal().item()
        duplicate_count = df.filter(df.is_duplicated()).height

        negative_amounts = 0
        invalid_transaction_types = 0

        # Protect execution against missing target columns
        if "amount" in df.columns:
            negative_amounts = df.filter(pl.col("amount") < 0).height

        if "type" in df.columns:
            invalid_transaction_types = df.filter(
                ~pl.col("type").is_in(cls.VALID_TRANSACTION_TYPES)
            ).height

        report = {
            "rows": rows,
            "columns": cols,
            "missing_values": null_count,
            "duplicate_rows": duplicate_count,
            "negative_amounts": negative_amounts,
            "invalid_transaction_types": invalid_transaction_types,
            "missing_columns": missing_cols,
            "valid": False,
        }

        report["valid"] = (
            len(report["missing_columns"]) == 0
            and report["missing_values"] == 0
            and report["negative_amounts"] == 0
            and report["invalid_transaction_types"] == 0
        )

        if report["valid"]:
            logger.success(f"Validation successful: {report}")
        else:
            logger.error(f"Validation failed: {report}")

        return report